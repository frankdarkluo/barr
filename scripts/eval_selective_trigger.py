#!/usr/bin/env python
import argparse
import csv
import glob
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ambig-input", required=True)
    parser.add_argument("--disambig-input", required=True)
    parser.add_argument("--ambig-eval-glob", required=True)
    parser.add_argument("--disambig-eval-glob", required=True)
    parser.add_argument("--condition", default="redirect")
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--target-trigger-min", type=float, default=0.10)
    parser.add_argument("--target-trigger-max", type=float, default=0.20)
    return parser.parse_args()


def read_jsonl(path: str) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("{"):
                rows.append(json.loads(line))
    return rows


def read_glob_jsonl(pattern: str) -> list[dict]:
    rows = []
    for path in sorted(glob.glob(pattern)):
        rows.extend(read_jsonl(path))
    return rows


def dedup_eval_rows(rows: list[dict]) -> dict[tuple[str, str], dict]:
    seen = {}
    for row in rows:
        key = (str(row["sample_id"]), row["condition"])
        if key not in seen:
            seen[key] = row
    return seen


def first_transition_index(row: dict) -> int:
    transition_points = row.get("transition_points") or []
    if not transition_points:
        return -1
    return int(transition_points[0]["token_index"])


def safe_rate(numer: int, denom: int) -> float:
    return numer / denom if denom else 0.0


def evaluate_threshold(
    threshold: int,
    ambig_rows: list[dict],
    disambig_rows: list[dict],
    ambig_eval: dict[tuple[str, str], dict],
    disambig_eval: dict[tuple[str, str], dict],
    condition: str,
) -> dict:
    total_rows = len(ambig_rows) + len(disambig_rows)
    trigger_count = 0

    ambig_biased_base = 0
    ambig_corrected = 0

    disambig_correct_base = 0
    disambig_harmed = 0

    for row in ambig_rows:
        sample_id = str(row["sample_id"])
        score = first_transition_index(row)
        triggered = score >= threshold
        if triggered:
            trigger_count += 1

        vanilla_label = ambig_eval[(sample_id, "vanilla")]["trajectory_label"]
        intervention_label = ambig_eval[(sample_id, condition)]["trajectory_label"]
        final_label = intervention_label if triggered else vanilla_label

        if vanilla_label == "biased":
            ambig_biased_base += 1
            if final_label == "correct":
                ambig_corrected += 1

    for row in disambig_rows:
        sample_id = str(row["sample_id"])
        score = first_transition_index(row)
        triggered = score >= threshold
        if triggered:
            trigger_count += 1

        vanilla_label = disambig_eval[(sample_id, "vanilla")]["trajectory_label"]
        intervention_label = disambig_eval[(sample_id, condition)]["trajectory_label"]
        final_label = intervention_label if triggered else vanilla_label

        if vanilla_label == "correct":
            disambig_correct_base += 1
            if final_label != "correct":
                disambig_harmed += 1

    return {
        "threshold": threshold,
        "condition": condition,
        "trigger_count": trigger_count,
        "trigger_rate": safe_rate(trigger_count, total_rows),
        "ambig_biased_base": ambig_biased_base,
        "ambig_corrected": ambig_corrected,
        "ambig_correction_rate": safe_rate(ambig_corrected, ambig_biased_base),
        "disambig_correct_base": disambig_correct_base,
        "disambig_harmed": disambig_harmed,
        "disambig_harm_rate": safe_rate(disambig_harmed, disambig_correct_base),
        "net_benefit": ambig_corrected - disambig_harmed,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def format_row(row: dict) -> str:
    return (
        f"| {row['threshold']} | {row['trigger_count']} | {row['trigger_rate']:.4f} | "
        f"{row['ambig_corrected']} | {row['ambig_correction_rate']:.4f} | "
        f"{row['disambig_harmed']} | {row['disambig_harm_rate']:.4f} | "
        f"{row['net_benefit']} |"
    )


def write_md(path: Path, summary: dict) -> None:
    lines = [
        "# Selective Trigger Evaluation",
        "",
        "Risk score: first transition token index",
        f"Intervention condition: `{summary['condition']}`",
        "",
        f"- Ambig biased base: `{summary['ambig_biased_base']}`",
        f"- Disambig correct base: `{summary['disambig_correct_base']}`",
        "",
        "## Best Net Benefit",
        "",
        "| threshold | trigger_count | trigger_rate | ambig_corrected | ambig_correction_rate | disambig_harmed | disambig_harm_rate | net_benefit |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        format_row(summary["best_net_benefit"]),
        "",
        "## Best In Target Trigger Band",
        "",
        f"Target band: `{summary['target_trigger_min']:.2f}` - `{summary['target_trigger_max']:.2f}`",
        "",
        "| threshold | trigger_count | trigger_rate | ambig_corrected | ambig_correction_rate | disambig_harmed | disambig_harm_rate | net_benefit |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        format_row(summary["best_in_band"]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    ambig_rows = read_jsonl(args.ambig_input)
    disambig_rows = read_jsonl(args.disambig_input)
    ambig_eval = dedup_eval_rows(read_glob_jsonl(args.ambig_eval_glob))
    disambig_eval = dedup_eval_rows(read_glob_jsonl(args.disambig_eval_glob))

    thresholds = sorted(
        {
            first_transition_index(row)
            for row in ambig_rows + disambig_rows
            if first_transition_index(row) >= 0
        }
    )
    sweep_rows = [
        evaluate_threshold(
            threshold=threshold,
            ambig_rows=ambig_rows,
            disambig_rows=disambig_rows,
            ambig_eval=ambig_eval,
            disambig_eval=disambig_eval,
            condition=args.condition,
        )
        for threshold in thresholds
    ]

    best_net_benefit = max(
        sweep_rows,
        key=lambda row: (row["net_benefit"], -row["disambig_harm_rate"], row["ambig_correction_rate"]),
    )
    in_band = [
        row
        for row in sweep_rows
        if args.target_trigger_min <= row["trigger_rate"] <= args.target_trigger_max
    ]
    best_in_band = max(
        in_band or sweep_rows,
        key=lambda row: (row["net_benefit"], row["ambig_correction_rate"], -row["disambig_harm_rate"]),
    )

    output_csv = Path(args.output_csv)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)

    write_csv(output_csv, sweep_rows)
    write_json(
        output_json,
        {
            "condition": args.condition,
            "score_name": "first_transition_index",
            "ambig_biased_base": sum(
                1 for row in ambig_rows if ambig_eval[(str(row["sample_id"]), "vanilla")]["trajectory_label"] == "biased"
            ),
            "disambig_correct_base": sum(
                1
                for row in disambig_rows
                if disambig_eval[(str(row["sample_id"]), "vanilla")]["trajectory_label"] == "correct"
            ),
            "target_trigger_min": args.target_trigger_min,
            "target_trigger_max": args.target_trigger_max,
            "best_net_benefit": best_net_benefit,
            "best_in_band": best_in_band,
        },
    )
    write_md(
        output_md,
        {
            "condition": args.condition,
            "ambig_biased_base": sum(
                1 for row in ambig_rows if ambig_eval[(str(row["sample_id"]), "vanilla")]["trajectory_label"] == "biased"
            ),
            "disambig_correct_base": sum(
                1
                for row in disambig_rows
                if disambig_eval[(str(row["sample_id"]), "vanilla")]["trajectory_label"] == "correct"
            ),
            "target_trigger_min": args.target_trigger_min,
            "target_trigger_max": args.target_trigger_max,
            "best_net_benefit": best_net_benefit,
            "best_in_band": best_in_band,
        },
    )

    print(f"Wrote sweep to {output_csv}")
    print(f"Wrote summary json to {output_json}")
    print(f"Wrote summary md to {output_md}")
    print(json.dumps({"best_net_benefit": best_net_benefit, "best_in_band": best_in_band}, ensure_ascii=False))


if __name__ == "__main__":
    main()
