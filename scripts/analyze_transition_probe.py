import argparse
import json
from pathlib import Path
import sys

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature_file", required=True)
    parser.add_argument(
        "--output_dir",
        default="outputs/transition_probe/analysis",
    )
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--weight_decay", type=float, default=1e-2)
    return parser.parse_args()


def standardize_train_test(X_train: np.ndarray, X_test: np.ndarray):
    mean = X_train.mean(axis=0, keepdims=True)
    std = X_train.std(axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    return (X_train - mean) / std, (X_test - mean) / std


def make_stratified_folds(y: np.ndarray, n_folds: int, seed: int):
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


def fit_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    steps: int,
    lr: float,
    weight_decay: float,
):
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


def compute_pca(X: np.ndarray, components: int = 2) -> np.ndarray:
    centered = X - X.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    basis = vt[:components].T
    return centered @ basis


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = np.load(args.feature_file, allow_pickle=True)
    X = payload["X"].astype(np.float32)
    y = payload["y"].astype(np.int64)
    sample_ids = payload["sample_ids"]
    categories = payload["categories"]
    labels = payload["labels"]

    folds = make_stratified_folds(y, args.folds, args.seed)
    fold_rows = []
    all_scores = np.zeros(len(y), dtype=np.float32)

    for fold_idx, (train_idx, test_idx) in enumerate(folds, start=1):
        X_train, X_test = standardize_train_test(X[train_idx], X[test_idx])
        probs = fit_logistic_regression(
            X_train,
            y[train_idx],
            X_test,
            steps=args.steps,
            lr=args.lr,
            weight_decay=args.weight_decay,
        )
        auc = roc_auc_score_manual(y[test_idx], probs)
        all_scores[test_idx] = probs
        fold_rows.append(
            {
                "fold": fold_idx,
                "test_size": int(len(test_idx)),
                "biased_in_test": int(y[test_idx].sum()),
                "auroc": round(auc, 6),
            }
        )

    overall_auc = roc_auc_score_manual(y, all_scores)
    pca_coords = compute_pca(X, components=2)
    pca_path = output_dir / f"{Path(args.feature_file).stem}_pca.jsonl"
    with pca_path.open("w", encoding="utf-8") as handle:
        for idx in range(len(y)):
            handle.write(
                json.dumps(
                    {
                        "sample_id": str(sample_ids[idx]),
                        "category": str(categories[idx]),
                        "trajectory_label": str(labels[idx]),
                        "target": int(y[idx]),
                        "pc1": float(pca_coords[idx, 0]),
                        "pc2": float(pca_coords[idx, 1]),
                        "probe_score": float(all_scores[idx]),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    results_path = output_dir / f"{Path(args.feature_file).stem}_probe_results.json"
    result = {
        "feature_file": args.feature_file,
        "n_samples": int(len(y)),
        "n_biased": int(y.sum()),
        "n_correct": int((y == 0).sum()),
        "folds": fold_rows,
        "mean_auroc": float(np.mean([row["auroc"] for row in fold_rows])),
        "std_auroc": float(np.std([row["auroc"] for row in fold_rows])),
        "overall_oof_auroc": float(overall_auc),
        "pca_output": str(pca_path),
    }
    results_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
