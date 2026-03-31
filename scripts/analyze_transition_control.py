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
        required=True,
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
    return parser.parse_args()


def read_jsonl(paths: list[Path]) -> list[dict]:
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


def select_hidden_dims(
    X_hidden_train: np.ndarray,
    X_hidden_test: np.ndarray,
    hidden_dims: int,
) -> tuple[np.ndarray, np.ndarray]:
    variance = X_hidden_train.var(axis=0)
    selected = np.argsort(variance)[-hidden_dims:]
    return X_hidden_train[:, selected], X_hidden_test[:, selected]


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
        train_parts = [X_position[train_idx]] if X_position.shape[1] else []
        test_parts = [X_position[test_idx]] if X_position.shape[1] else []
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


def load_examples(rows: list[dict]) -> list[dict]:
    examples = []
    for row in rows:
        label = row.get("trajectory_label")
        transitions = row.get("transition_points") or []
        control = row.get("matched_control_point")
        if label not in {"correct", "biased"} or not transitions or not control:
            continue

        transition_payload = torch.load(Path(transitions[0]["tensor_path"]), map_location="cpu")
        control_payload = torch.load(Path(control["tensor_path"]), map_location="cpu")
        examples.append(
            {
                "sample_id": row["sample_id"],
                "category": row["category"],
                "target": 1 if label == "biased" else 0,
                "transition_hidden": transition_payload["layer_-1"].reshape(-1).numpy().astype(np.float32),
                "control_hidden": control_payload["layer_-1"].reshape(-1).numpy().astype(np.float32),
                "transition_position": np.asarray(
                    [
                        int(transitions[0]["token_index"]),
                        int(transitions[0]["token_index"]) / max(int(row.get("generated_tokens") or 1), 1),
                    ],
                    dtype=np.float32,
                ),
                "control_position": np.asarray(
                    [
                        int(control["token_index"]),
                        int(control["token_index"]) / max(int(control.get("response_token_count") or 1), 1),
                    ],
                    dtype=np.float32,
                ),
                "control_distance": int(control["distance_from_first_transition"]),
                "transition_alignment_cosine": control.get("transition_alignment_cosine"),
            }
        )
    return examples


def write_markdown(output_path: Path, summary: dict) -> None:
    lines = [
        "# Transition vs Control Summary",
        "",
        "## Dataset",
        f"- Usable rows: `{summary['dataset']['usable_rows']}`",
        f"- Correct: `{summary['dataset']['correct']}`",
        f"- Biased: `{summary['dataset']['biased']}`",
        f"- Mean control distance: `{summary['dataset']['mean_control_distance']:.4f}`",
        f"- Mean transition alignment cosine: `{summary['dataset']['mean_transition_alignment_cosine']:.4f}`",
        "",
        "## Results",
    ]
    for row in summary["results"]:
        lines.append(
            f"- `{row['name']}`: mean `{row['mean_auroc']:.4f}`, std `{row['std_auroc']:.4f}`, OOF `{row['overall_oof_auroc']:.4f}`"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = read_jsonl([Path(path) for path in args.inputs])
    examples = load_examples(rows)
    y = np.asarray([example["target"] for example in examples], dtype=np.int64)
    folds = stratified_folds(y, args.folds, args.seed)

    X_transition_hidden = np.stack([example["transition_hidden"] for example in examples], axis=0)
    X_control_hidden = np.stack([example["control_hidden"] for example in examples], axis=0)
    X_transition_position = np.stack([example["transition_position"] for example in examples], axis=0)
    X_control_position = np.stack([example["control_position"] for example in examples], axis=0)

    results = [
        evaluate_cv(
            name="transition_hidden_top64_only",
            X_position=np.zeros((len(examples), 0), dtype=np.float32),
            X_hidden=X_transition_hidden,
            y=y,
            folds=folds,
            hidden_dims=args.hidden_dims,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        ),
        evaluate_cv(
            name="control_hidden_top64_only",
            X_position=np.zeros((len(examples), 0), dtype=np.float32),
            X_hidden=X_control_hidden,
            y=y,
            folds=folds,
            hidden_dims=args.hidden_dims,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        ),
        evaluate_cv(
            name="transition_position_plus_hidden_top64",
            X_position=X_transition_position,
            X_hidden=X_transition_hidden,
            y=y,
            folds=folds,
            hidden_dims=args.hidden_dims,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        ),
        evaluate_cv(
            name="control_position_plus_hidden_top64",
            X_position=X_control_position,
            X_hidden=X_control_hidden,
            y=y,
            folds=folds,
            hidden_dims=args.hidden_dims,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        ),
    ]

    summary = {
        "dataset": {
            "usable_rows": int(len(examples)),
            "correct": int((y == 0).sum()),
            "biased": int((y == 1).sum()),
            "mean_control_distance": float(
                np.mean([example["control_distance"] for example in examples])
            ),
            "distance_histogram": dict(
                sorted(Counter(example["control_distance"] for example in examples).items())
            ),
            "mean_transition_alignment_cosine": float(
                np.mean(
                    [
                        example["transition_alignment_cosine"]
                        for example in examples
                        if example["transition_alignment_cosine"] is not None
                    ]
                )
            ),
        },
        "results": results,
    }

    json_path = output_dir / "transition_control_results.json"
    md_path = output_dir / "transition_control_summary.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved {json_path}")
    print(f"Saved {md_path}")


if __name__ == "__main__":
    main()
