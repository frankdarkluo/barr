#!/usr/bin/env python
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from barr.config import load_yaml
from barr.io_utils import read_jsonl, write_csv, write_jsonl


def read_csv_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def mean(values):
    return sum(values) / len(values) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/week1_pilot.yaml")
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    task_rows = read_csv_rows(Path(config["paths"]["task_metrics_path"]))
    fairness_rows = read_csv_rows(Path(config["paths"]["fairness_metrics_path"]))
    group_gap_rows = read_csv_rows(Path(config["paths"]["group_gap_path"]))
    counterfactual_rows = read_csv_rows(Path(config["paths"]["counterfactual_gap_path"]))
    reasoning_rows = read_csv_rows(Path(config["paths"]["reasoning_features_path"]))

    inference_rows = []
    for input_path in args.inputs:
        inference_rows.extend(read_jsonl(Path(input_path)))

    main_table_rows = []
    for row in task_rows:
        main_table_rows.append(
            {
                "model_name": row["model_name"],
                "quant_method": row["quant_method"],
                "dataset_name": row["dataset_name"],
                "language": row["language"],
                "accuracy": row["accuracy"],
                "unknown_rate": row["unknown_rate"],
                "bias_score": row["bias_score"],
                "parse_success_rate": row.get("parse_success_rate", ""),
            }
        )

    per_language_rows = []
    grouped_reasoning = defaultdict(list)
    for row in reasoning_rows:
        key = (row["model_name"], row["quant_method"], row["dataset_name"], row["language"])
        grouped_reasoning[key].append(row)
    grouped_counterfactual = defaultdict(list)
    for row in counterfactual_rows:
        key = (row["model_name"], row["quant_method"], row["dataset_name"], row["language"])
        grouped_counterfactual[key].append(row)
    grouped_gap = defaultdict(list)
    for row in group_gap_rows:
        key = (row["model_name"], row["quant_method"], row["dataset_name"], row["language"])
        grouped_gap[key].append(row)

    for row in task_rows:
        key = (row["model_name"], row["quant_method"], row["dataset_name"], row["language"])
        reasoning_subset = grouped_reasoning.get(key, [])
        counter_subset = grouped_counterfactual.get(key, [])
        gap_subset = grouped_gap.get(key, [])
        per_language_rows.append(
            {
                "model_name": row["model_name"],
                "quant_method": row["quant_method"],
                "dataset_name": row["dataset_name"],
                "language": row["language"],
                "accuracy": row["accuracy"],
                "unknown_rate": row["unknown_rate"],
                "bias_score": row["bias_score"],
                "answer_flip_rate": mean([float(item["answer_flip_rate"]) for item in counter_subset]),
                "group_gap_bias_score": mean([float(item["bias_score_gap"]) for item in gap_subset]),
                "mean_think_token_length": mean([float(item["think_token_length"]) for item in reasoning_subset]),
                "mean_latency": mean([float(item["latency"]) for item in reasoning_subset if item["latency"] != ""]),
            }
        )

    write_csv(
        Path(config["paths"]["week1_main_table_path"]),
        main_table_rows,
        fieldnames=[
            "model_name",
            "quant_method",
            "dataset_name",
            "language",
            "accuracy",
            "unknown_rate",
            "bias_score",
            "parse_success_rate",
        ],
    )
    write_csv(
        Path(config["paths"]["week1_per_language_table_path"]),
        per_language_rows,
        fieldnames=[
            "model_name",
            "quant_method",
            "dataset_name",
            "language",
            "accuracy",
            "unknown_rate",
            "bias_score",
            "answer_flip_rate",
            "group_gap_bias_score",
            "mean_think_token_length",
            "mean_latency",
        ],
    )

    bf16_rows = {
        (row["sample_id"], row["dataset_name"]): row
        for row in inference_rows
        if row["quant_method"].lower() == "bf16"
    }
    case_rows = []
    for row in inference_rows:
        if row["quant_method"].lower() == "bf16":
            continue
        baseline = bf16_rows.get((row["sample_id"], row["dataset_name"]))
        if not baseline:
            continue
        baseline_biased = baseline["final_answer"] == baseline.get("stereotype_label")
        current_biased = row["final_answer"] == row.get("stereotype_label")
        if (not baseline_biased) and current_biased:
            case_rows.append(
                {
                    "sample_id": row["sample_id"],
                    "dataset_name": row["dataset_name"],
                    "language": row["language"],
                    "category": row["category"],
                    "quant_method": row["quant_method"],
                    "baseline_answer": baseline["final_answer"],
                    "quantized_answer": row["final_answer"],
                    "baseline_reasoning": baseline["reasoning_text"],
                    "quantized_reasoning": row["reasoning_text"],
                    "context": row["context"],
                    "question": row["question"],
                }
            )
    write_jsonl(Path(config["paths"]["week1_cases_path"]), case_rows)

    summary_lines = [
        "# Week 1 Summary",
        "",
        "## Main findings",
        "",
        f"- Evaluated {len(main_table_rows)} model x dataset x language slices.",
        f"- Collected {len(counterfactual_rows)} paired counterfactual comparisons.",
        f"- Collected {len(case_rows)} candidate BF16-normal but quantized-biased cases.",
        "",
        "## Pilot tables",
        "",
        f"- main_table.csv: {config['paths']['week1_main_table_path']}",
        f"- per_language_table.csv: {config['paths']['week1_per_language_table_path']}",
        f"- case_studies.jsonl: {config['paths']['week1_cases_path']}",
        "",
        "## Notes",
        "",
        "- Entropy / TECA fields are scaffolded but remain empty unless logits are exposed by the inference backend.",
        "- OpenMBBQ is implemented as an open-style prompt variant with forced final A/B/C answer tags.",
    ]
    Path(config["paths"]["week1_summary_path"]).write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Wrote summary artifacts to {Path(config['paths']['week1_summary_path']).parent}")


if __name__ == "__main__":
    main()

