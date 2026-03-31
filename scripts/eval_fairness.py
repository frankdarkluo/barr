#!/usr/bin/env python
import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from barr.config import load_yaml
from barr.io_utils import read_jsonl, write_csv


def aggregate_metrics(rows: List[Dict], group_fields: List[str]) -> List[Dict]:
    grouped: Dict[tuple, List[Dict]] = defaultdict(list)
    for row in rows:
        key = tuple(row[field] for field in group_fields)
        grouped[key].append(row)

    output = []
    for key, items in sorted(grouped.items()):
        total = len(items)
        correct = sum(1 for row in items if row["final_answer"] == row["accuracy_label"])
        unknown = sum(1 for row in items if row["final_answer"] == row.get("unknown_label"))
        biased = sum(1 for row in items if row["final_answer"] == row.get("stereotype_label"))
        row = dict(zip(group_fields, key))
        row.update(
            {
                "n": total,
                "accuracy": correct / total if total else 0.0,
                "unknown_rate": unknown / total if total else 0.0,
                "bias_score": biased / total if total else 0.0,
                "parse_success_rate": sum(1 for row in items if row.get("parse_success")) / total if total else 0.0,
            }
        )
        output.append(row)
    return output


def compute_group_gap(rows: List[Dict]) -> List[Dict]:
    grouped: Dict[tuple, List[Dict]] = defaultdict(list)
    for row in rows:
        if row.get("pair_group_id"):
            key = (row["model_name"], row["quant_method"], row["dataset_name"], row["language"], row["category"], row["pair_group_id"])
            grouped[key].append(row)

    output = []
    for key, items in sorted(grouped.items()):
        if len(items) != 2:
            continue
        first, second = sorted(items, key=lambda row: row["sample_id"])
        first_correct = int(first["final_answer"] == first["accuracy_label"])
        second_correct = int(second["final_answer"] == second["accuracy_label"])
        first_unknown = int(first["final_answer"] == first.get("unknown_label"))
        second_unknown = int(second["final_answer"] == second.get("unknown_label"))
        first_bias = int(first["final_answer"] == first.get("stereotype_label"))
        second_bias = int(second["final_answer"] == second.get("stereotype_label"))
        output.append(
            {
                "model_name": first["model_name"],
                "quant_method": first["quant_method"],
                "dataset_name": first["dataset_name"],
                "language": first["language"],
                "category": first["category"],
                "pair_group_id": first["pair_group_id"],
                "sample_id_a": first["sample_id"],
                "sample_id_b": second["sample_id"],
                "accuracy_gap": abs(first_correct - second_correct),
                "unknown_rate_gap": abs(first_unknown - second_unknown),
                "bias_score_gap": abs(first_bias - second_bias),
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/week1_pilot.yaml")
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    all_rows = []
    for input_path in args.inputs:
        all_rows.extend(read_jsonl(Path(input_path)))

    fairness_rows = aggregate_metrics(
        all_rows,
        ["model_name", "quant_method", "dataset_name", "language", "category"],
    )
    summary_rows = aggregate_metrics(
        all_rows,
        ["model_name", "quant_method", "dataset_name", "language"],
    )
    group_gap_rows = compute_group_gap(all_rows)

    write_csv(
        Path(config["paths"]["fairness_metrics_path"]),
        fairness_rows,
        fieldnames=[
            "model_name",
            "quant_method",
            "dataset_name",
            "language",
            "category",
            "n",
            "accuracy",
            "unknown_rate",
            "bias_score",
            "parse_success_rate",
        ],
    )
    write_csv(
        Path(config["paths"]["task_metrics_path"]),
        summary_rows,
        fieldnames=[
            "model_name",
            "quant_method",
            "dataset_name",
            "language",
            "n",
            "accuracy",
            "unknown_rate",
            "bias_score",
            "parse_success_rate",
        ],
    )
    write_csv(
        Path(config["paths"]["group_gap_path"]),
        group_gap_rows,
        fieldnames=[
            "model_name",
            "quant_method",
            "dataset_name",
            "language",
            "category",
            "pair_group_id",
            "sample_id_a",
            "sample_id_b",
            "accuracy_gap",
            "unknown_rate_gap",
            "bias_score_gap",
        ],
    )
    print(
        f"Wrote fairness metrics to {config['paths']['fairness_metrics_path']}, "
        f"{config['paths']['task_metrics_path']}, and {config['paths']['group_gap_path']}"
    )


if __name__ == "__main__":
    main()

