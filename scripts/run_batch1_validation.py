import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "outputs/transition_probe/raw/seed_0_full_v2.jsonl",
            "outputs/transition_probe/raw/seed_1_full.jsonl",
            "outputs/transition_probe/raw/seed_2_full.jsonl",
        ],
    )
    parser.add_argument(
        "--output_dir",
        default="outputs/transition_probe/analysis",
    )
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--weight_decay", type=float, default=1e-2)
    parser.add_argument("--hidden_dims", type=int, default=64)
    parser.add_argument("--group_by_sample", action="store_true")
    return parser.parse_args()


def load_rows(paths: list[Path]) -> list[dict]:
    rows = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("{"):
                    row = json.loads(line)
                    row["_source_file"] = path.name
                    rows.append(row)
    return rows


def build_examples(rows: list[dict]) -> list[dict]:
    examples = []
    for row in rows:
        label = row.get("trajectory_label")
        transitions = row.get("transition_points") or []
        if label not in {"correct", "biased"} or not transitions:
            continue

        first = transitions[0]
        tensor_path = Path(first["tensor_path"])
        if not tensor_path.exists():
            continue

        payload = torch.load(tensor_path, map_location="cpu")
        hidden = payload["layer_-1"].reshape(-1).numpy().astype(np.float32)
        generated_tokens = max(int(row.get("generated_tokens") or 1), 1)
        token_index = int(first.get("token_index") or first.get("step") or 0)

        examples.append(
            {
                "sample_id": row["sample_id"],
                "category": row["category"],
                "source_file": row["_source_file"],
                "target": 1 if label == "biased" else 0,
                "hidden": hidden,
                "position": np.asarray(
                    [token_index, token_index / generated_tokens],
                    dtype=np.float32,
                ),
                "prefix_len": np.asarray(
                    [len(first.get("prefix_text") or "")],
                    dtype=np.float32,
                ),
            }
        )
    return examples


def standardize_train_test(X_train: np.ndarray, X_test: np.ndarray):
    mean = X_train.mean(axis=0, keepdims=True)
    std = X_train.std(axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    return (X_train - mean) / std, (X_test - mean) / std


def roc_auc_score_manual(y_true: np.ndarray, y_score: np.ndarray) -> float:
    order = np.argsort(y_score)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(y_score) + 1)

    unique_scores, inverse = np.unique(y_score, return_inverse=True)
    for idx in range(len(unique_scores)):
        mask = inverse == idx
        if mask.sum() > 1:
            ranks[mask] = ranks[mask].mean()

    pos_mask = y_true == 1
    n_pos = pos_mask.sum()
    n_neg = (y_true == 0).sum()
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    rank_sum = ranks[pos_mask].sum()
    return float((rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def fit_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    steps: int,
    lr: float,
    weight_decay: float,
) -> np.ndarray:
    x_train = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train.reshape(-1, 1), dtype=torch.float32)
    x_test = torch.tensor(X_test, dtype=torch.float32)

    model = torch.nn.Linear(X_train.shape[1], 1)
    pos = float(y_train.sum())
    neg = float(len(y_train) - y_train.sum())
    pos_weight = torch.tensor([neg / max(pos, 1.0)], dtype=torch.float32)
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        logits = model(x_train)
        loss = loss_fn(logits, y_train_t)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        probs = torch.sigmoid(model(x_test)).reshape(-1).cpu().numpy()
    return probs


def select_hidden_dims(
    X_hidden_train: np.ndarray,
    X_hidden_test: np.ndarray,
    hidden_dims: int,
) -> tuple[np.ndarray, np.ndarray]:
    variance = X_hidden_train.var(axis=0)
    selected = np.argsort(variance)[-hidden_dims:]
    return X_hidden_train[:, selected], X_hidden_test[:, selected]


def stratified_folds(y: np.ndarray, n_folds: int, seed: int):
    rng = np.random.default_rng(seed)
    pos = np.where(y == 1)[0]
    neg = np.where(y == 0)[0]
    rng.shuffle(pos)
    rng.shuffle(neg)
    pos_folds = np.array_split(pos, n_folds)
    neg_folds = np.array_split(neg, n_folds)
    folds = []
    for fold_idx in range(n_folds):
        test_idx = np.concatenate([pos_folds[fold_idx], neg_folds[fold_idx]])
        train_mask = np.ones(len(y), dtype=bool)
        train_mask[test_idx] = False
        train_idx = np.where(train_mask)[0]
        folds.append((train_idx, test_idx))
    return folds


def group_stratified_folds(
    sample_ids: np.ndarray,
    y: np.ndarray,
    n_folds: int,
    seed: int,
):
    rng = np.random.default_rng(seed)
    unique_ids = sorted(set(sample_ids.tolist()))
    group_to_indices = {sample_id: np.where(sample_ids == sample_id)[0] for sample_id in unique_ids}
    positive_groups = [sample_id for sample_id in unique_ids if int(y[group_to_indices[sample_id]].max()) == 1]
    negative_groups = [sample_id for sample_id in unique_ids if int(y[group_to_indices[sample_id]].max()) == 0]
    rng.shuffle(positive_groups)
    rng.shuffle(negative_groups)
    pos_folds = np.array_split(np.asarray(positive_groups, dtype=object), n_folds)
    neg_folds = np.array_split(np.asarray(negative_groups, dtype=object), n_folds)

    folds = []
    for fold_idx in range(n_folds):
        test_groups = list(pos_folds[fold_idx]) + list(neg_folds[fold_idx])
        test_idx = np.concatenate([group_to_indices[group] for group in test_groups])
        train_mask = np.ones(len(y), dtype=bool)
        train_mask[test_idx] = False
        train_idx = np.where(train_mask)[0]
        folds.append((train_idx, test_idx))
    return folds


def stack_feature(examples: list[dict], key: str) -> np.ndarray:
    return np.stack([example[key] for example in examples], axis=0)


def evaluate_cv(
    name: str,
    X_position: np.ndarray,
    X_hidden: np.ndarray | None,
    y: np.ndarray,
    folds: list[tuple[np.ndarray, np.ndarray]],
    hidden_dims: int,
    steps: int,
    lr: float,
    weight_decay: float,
) -> dict:
    fold_rows = []
    oof_scores = np.zeros(len(y), dtype=np.float32)

    for fold_idx, (train_idx, test_idx) in enumerate(folds, start=1):
        train_parts = [X_position[train_idx]]
        test_parts = [X_position[test_idx]]

        if X_hidden is not None:
            train_hidden, test_hidden = select_hidden_dims(
                X_hidden[train_idx],
                X_hidden[test_idx],
                hidden_dims=hidden_dims,
            )
            train_parts.append(train_hidden)
            test_parts.append(test_hidden)

        X_train = np.concatenate(train_parts, axis=1)
        X_test = np.concatenate(test_parts, axis=1)
        X_train, X_test = standardize_train_test(X_train, X_test)
        probs = fit_logistic_regression(
            X_train,
            y[train_idx],
            X_test,
            steps=steps,
            lr=lr,
            weight_decay=weight_decay,
        )
        auc = roc_auc_score_manual(y[test_idx], probs)
        oof_scores[test_idx] = probs
        fold_rows.append(
            {
                "fold": fold_idx,
                "test_size": int(len(test_idx)),
                "biased_in_test": int(y[test_idx].sum()),
                "auroc": float(auc),
            }
        )

    return {
        "name": name,
        "folds": fold_rows,
        "mean_auroc": float(np.mean([row["auroc"] for row in fold_rows])),
        "std_auroc": float(np.std([row["auroc"] for row in fold_rows])),
        "overall_oof_auroc": float(roc_auc_score_manual(y, oof_scores)),
    }


def evaluate_loco(
    categories: list[str],
    examples: list[dict],
    y: np.ndarray,
    X_position: np.ndarray,
    X_hidden: np.ndarray,
    hidden_dims: int,
    steps: int,
    lr: float,
    weight_decay: float,
) -> list[dict]:
    results = []
    example_categories = np.asarray([example["category"] for example in examples], dtype=object)

    for held_out in categories:
        test_idx = np.where(example_categories == held_out)[0]
        train_idx = np.where(example_categories != held_out)[0]
        if len(test_idx) == 0:
            continue

        y_train = y[train_idx]
        y_test = y[test_idx]
        if y_train.sum() == 0 or y_test.sum() == 0 or (y_test == 0).sum() == 0:
            results.append(
                {
                    "held_out_category": held_out,
                    "n_train": int(len(train_idx)),
                    "n_test": int(len(test_idx)),
                    "biased_in_train": int(y_train.sum()),
                    "biased_in_test": int(y_test.sum()),
                    "position_only_auroc": None,
                    "position_plus_hidden_auroc": None,
                    "delta_hidden_minus_position": None,
                    "status": "insufficient_positive_support",
                }
            )
            continue

        X_train_pos, X_test_pos = standardize_train_test(
            X_position[train_idx],
            X_position[test_idx],
        )
        pos_probs = fit_logistic_regression(
            X_train_pos,
            y_train,
            X_test_pos,
            steps=steps,
            lr=lr,
            weight_decay=weight_decay,
        )
        pos_auc = roc_auc_score_manual(y_test, pos_probs)

        train_hidden, test_hidden = select_hidden_dims(
            X_hidden[train_idx],
            X_hidden[test_idx],
            hidden_dims=hidden_dims,
        )
        X_train_combo = np.concatenate([X_position[train_idx], train_hidden], axis=1)
        X_test_combo = np.concatenate([X_position[test_idx], test_hidden], axis=1)
        X_train_combo, X_test_combo = standardize_train_test(X_train_combo, X_test_combo)
        combo_probs = fit_logistic_regression(
            X_train_combo,
            y_train,
            X_test_combo,
            steps=steps,
            lr=lr,
            weight_decay=weight_decay,
        )
        combo_auc = roc_auc_score_manual(y_test, combo_probs)

        results.append(
            {
                "held_out_category": held_out,
                "n_train": int(len(train_idx)),
                "n_test": int(len(test_idx)),
                "biased_in_train": int(y_train.sum()),
                "biased_in_test": int(y_test.sum()),
                "position_only_auroc": float(pos_auc),
                "position_plus_hidden_auroc": float(combo_auc),
                "delta_hidden_minus_position": float(combo_auc - pos_auc),
                "status": "ok",
            }
        )

    return results


def write_markdown_report(
    output_path: Path,
    collection_summary: dict,
    probe_dataset: dict,
    cv_results: list[dict],
    biased_hist: dict,
    loco_rows: list[dict],
) -> None:
    lines = [
        "# Batch-1 Validation Summary",
        "",
        "## Collection Summary",
        f"- Total rows: `{collection_summary['total_rows']}`",
    ]
    for name, summary in collection_summary["by_file"].items():
        lines.append(
            f"- `{name}`: rows `{summary['rows']}`, parse `{summary['parse_success']}`, transition `{summary['with_transition']}`, labels `{summary['labels']}`"
        )

    lines.extend(
        [
            "",
            "## Probe Dataset",
            f"- Usable rows: `{probe_dataset['usable_rows']}`",
            f"- Correct: `{probe_dataset['correct']}`",
            f"- Biased: `{probe_dataset['biased']}`",
            f"- Biased category histogram: `{biased_hist}`",
            "",
            "## 5-Fold CV",
        ]
    )
    for row in cv_results:
        lines.append(
            f"- `{row['name']}`: mean `{row['mean_auroc']:.4f}`, std `{row['std_auroc']:.4f}`, OOF `{row['overall_oof_auroc']:.4f}`"
        )

    lines.extend(["", "## Leave-One-Category-Out"])
    for row in loco_rows:
        if row["status"] != "ok":
            lines.append(
                f"- `{row['held_out_category']}`: skipped, biased_in_test `{row['biased_in_test']}`"
            )
            continue
        lines.append(
            f"- `{row['held_out_category']}`: position `{row['position_only_auroc']:.4f}`, position+hidden `{row['position_plus_hidden_auroc']:.4f}`, delta `{row['delta_hidden_minus_position']:+.4f}`, biased_in_test `{row['biased_in_test']}`"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_paths = [Path(path) for path in args.inputs]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(input_paths)
    collection_summary = {"total_rows": len(rows), "by_file": {}}
    for path in input_paths:
        subset = [row for row in rows if row["_source_file"] == path.name]
        labels = Counter(row.get("trajectory_label", "missing") for row in subset)
        collection_summary["by_file"][path.name] = {
            "rows": len(subset),
            "parse_success": int(sum(bool(row.get("parse_success")) for row in subset)),
            "with_transition": int(sum(bool(row.get("transition_points")) for row in subset)),
            "labels": dict(labels),
        }

    examples = build_examples(rows)
    y = np.asarray([example["target"] for example in examples], dtype=np.int64)
    sample_ids = np.asarray([example["sample_id"] for example in examples], dtype=object)
    X_position = stack_feature(examples, "position")
    X_hidden = stack_feature(examples, "hidden")
    biased_hist = dict(
        sorted(
            Counter(
                example["category"] for example in examples if example["target"] == 1
            ).items()
        )
    )
    probe_dataset = {
        "usable_rows": int(len(examples)),
        "correct": int((y == 0).sum()),
        "biased": int((y == 1).sum()),
    }

    folds = (
        group_stratified_folds(sample_ids, y, args.folds, args.seed)
        if args.group_by_sample
        else stratified_folds(y, args.folds, args.seed)
    )
    cv_results = [
        evaluate_cv(
            name="position_only",
            X_position=X_position,
            X_hidden=None,
            y=y,
            folds=folds,
            hidden_dims=args.hidden_dims,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        ),
        evaluate_cv(
            name="position_plus_hidden_top64",
            X_position=X_position,
            X_hidden=X_hidden,
            y=y,
            folds=folds,
            hidden_dims=args.hidden_dims,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        ),
        evaluate_cv(
            name="hidden_top64_only",
            X_position=np.zeros((len(examples), 0), dtype=np.float32),
            X_hidden=X_hidden,
            y=y,
            folds=folds,
            hidden_dims=args.hidden_dims,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        ),
    ]

    categories = sorted({example["category"] for example in examples})
    loco_rows = evaluate_loco(
        categories=categories,
        examples=examples,
        y=y,
        X_position=X_position,
        X_hidden=X_hidden,
        hidden_dims=args.hidden_dims,
        steps=args.steps,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    results = {
        "collection_summary": collection_summary,
        "probe_dataset": probe_dataset,
        "biased_category_hist": biased_hist,
        "cv_results": cv_results,
        "loco_results": loco_rows,
        "config": {
            "folds": args.folds,
            "seed": args.seed,
            "steps": args.steps,
            "lr": args.lr,
            "weight_decay": args.weight_decay,
            "hidden_dims": args.hidden_dims,
            "group_by_sample": args.group_by_sample,
        },
    }

    stem = "batch1_validation_grouped" if args.group_by_sample else "batch1_validation"
    json_path = output_dir / f"{stem}_results.json"
    md_path = output_dir / f"{stem}_summary.md"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(
        output_path=md_path,
        collection_summary=collection_summary,
        probe_dataset=probe_dataset,
        cv_results=cv_results,
        biased_hist=biased_hist,
        loco_rows=loco_rows,
    )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Saved {json_path}")
    print(f"Saved {md_path}")


if __name__ == "__main__":
    main()
