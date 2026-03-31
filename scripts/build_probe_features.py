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
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--output_dir",
        default="outputs/transition_probe/features",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(line) for line in input_path.open(encoding="utf-8") if line.strip().startswith("{")]

    feature_rows = []
    x_last = []
    x_last4 = []
    y = []
    sample_ids = []
    categories = []
    labels = []

    for row in rows:
        label = row.get("trajectory_label")
        if label not in {"correct", "biased"}:
            continue
        transitions = row.get("transition_points") or []
        if not transitions:
            continue

        first = transitions[0]
        tensor_path = Path(first["tensor_path"])
        if not tensor_path.exists():
            continue
        payload = torch.load(tensor_path, map_location="cpu")
        last = payload["layer_-1"].reshape(-1).numpy()
        last4 = np.concatenate(
            [payload[f"layer_-{offset}"].reshape(-1).numpy() for offset in range(1, 5)],
            axis=0,
        )

        target = 1 if label == "biased" else 0
        x_last.append(last.astype(np.float32))
        x_last4.append(last4.astype(np.float32))
        y.append(target)
        sample_ids.append(row["sample_id"])
        categories.append(row["category"])
        labels.append(label)
        feature_rows.append(
            {
                "sample_id": row["sample_id"],
                "category": row["category"],
                "trajectory_label": label,
                "target": target,
                "tensor_path": str(tensor_path),
                "generated_tokens": row.get("generated_tokens"),
                "transition_count": len(transitions),
            }
        )

    manifest_path = output_dir / "feature_manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as handle:
        for row in feature_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    np.savez(
        output_dir / "first_transition_last_layer.npz",
        X=np.stack(x_last),
        y=np.asarray(y, dtype=np.int64),
        sample_ids=np.asarray(sample_ids, dtype=object),
        categories=np.asarray(categories, dtype=object),
        labels=np.asarray(labels, dtype=object),
    )
    np.savez(
        output_dir / "first_transition_last4_concat.npz",
        X=np.stack(x_last4),
        y=np.asarray(y, dtype=np.int64),
        sample_ids=np.asarray(sample_ids, dtype=object),
        categories=np.asarray(categories, dtype=object),
        labels=np.asarray(labels, dtype=object),
    )

    print(f"Saved {len(feature_rows)} feature rows to {output_dir}")
    print(json.dumps({"correct": int(sum(v == 0 for v in y)), "biased": int(sum(v == 1 for v in y))}, indent=2))


if __name__ == "__main__":
    main()
