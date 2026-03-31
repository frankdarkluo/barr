#!/usr/bin/env python
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ambig-inputs", nargs="+", required=True)
    parser.add_argument("--disambig-inputs", nargs="+", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-md", required=True)
    return parser.parse_args()


def read_jsonl(paths: list[str]) -> list[dict]:
    rows = []
    for path in paths:
        with Path(path).open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("{"):
                    rows.append(json.loads(line))
    return rows


def dedup(rows: list[dict]) -> list[dict]:
    seen = {}
    for row in rows:
        key = (str(row.get("sample_id")), str(row.get("condition")))
        if key not in seen:
            seen[key] = row
    return list(seen.values())


def build_maps(rows: list[dict]):
    label_map = defaultdict(dict)
    token_map = defaultdict(dict)
    for row in rows:
        sid = str(row["sample_id"])
        cond = row["condition"]
        label_map[cond][sid] = row.get("trajectory_label")
        token_map[cond][sid] = int(row.get("generated_tokens", 0))
    return label_map, token_map


def safe_rate(numer: int, denom: int) -> float:
    return (numer / denom) if denom else 0.0


def summarize_ambig(rows: list[dict]) -> list[dict]:
    label_map, token_map = build_maps(rows)
    vanilla = label_map.get("vanilla", {})
    biased_ids = [sid for sid, label in vanilla.items() if label == "biased"]

    out = []
    for cond in sorted(label_map.keys()):
        if cond == "vanilla":
            continue
        cond_labels = label_map[cond]
        corrected = sum(1 for sid in biased_ids if cond_labels.get(sid) == "correct")
        escaped = sum(1 for sid in biased_ids if cond_labels.get(sid) != "biased")
        tokens = [token_map[cond].get(sid, 0) for sid in biased_ids if sid in token_map[cond]]
        out.append(
            {
                "split": "ambig",
                "condition": cond,
                "focus": "biased_trajectories",
                "n_base": len(biased_ids),
                "corrected_to_correct": corrected,
                "corrected_rate": safe_rate(corrected, len(biased_ids)),
                "escaped_biased": escaped,
                "escaped_rate": safe_rate(escaped, len(biased_ids)),
                "avg_generated_tokens_on_base": mean(tokens) if tokens else 0.0,
            }
        )
    return out


def summarize_disambig(rows: list[dict]) -> list[dict]:
    label_map, token_map = build_maps(rows)
    vanilla = label_map.get("vanilla", {})
    correct_ids = [sid for sid, label in vanilla.items() if label == "correct"]

    out = []
    for cond in sorted(label_map.keys()):
        if cond == "vanilla":
            continue
        cond_labels = label_map[cond]
        harmed = sum(1 for sid in correct_ids if cond_labels.get(sid) != "correct")
        harmed_to_biased = sum(1 for sid in correct_ids if cond_labels.get(sid) == "biased")
        tokens = [token_map[cond].get(sid, 0) for sid in correct_ids if sid in token_map[cond]]
        out.append(
            {
                "split": "disambig",
                "condition": cond,
                "focus": "originally_correct",
                "n_base": len(correct_ids),
                "harmed": harmed,
                "harm_rate": safe_rate(harmed, len(correct_ids)),
                "harmed_to_biased": harmed_to_biased,
                "harmed_to_biased_rate": safe_rate(harmed_to_biased, len(correct_ids)),
                "avg_generated_tokens_on_base": mean(tokens) if tokens else 0.0,
            }
        )
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# AWQ Age Intervention Main Table", ""]
    for split in ["ambig", "disambig"]:
        subset = [row for row in rows if row["split"] == split]
        lines.append(f"## {split}")
        lines.append("")
        if split == "ambig":
            lines.append("| condition | n_base | corrected_to_correct | corrected_rate | escaped_biased | escaped_rate | avg_generated_tokens_on_base |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|")
            for row in subset:
                lines.append(
                    f"| {row['condition']} | {row['n_base']} | {row['corrected_to_correct']} | {row['corrected_rate']:.4f} | {row['escaped_biased']} | {row['escaped_rate']:.4f} | {row['avg_generated_tokens_on_base']:.2f} |"
                )
        else:
            lines.append("| condition | n_base | harmed | harm_rate | harmed_to_biased | harmed_to_biased_rate | avg_generated_tokens_on_base |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|")
            for row in subset:
                lines.append(
                    f"| {row['condition']} | {row['n_base']} | {row['harmed']} | {row['harm_rate']:.4f} | {row['harmed_to_biased']} | {row['harmed_to_biased_rate']:.4f} | {row['avg_generated_tokens_on_base']:.2f} |"
                )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    ambig_rows = dedup(read_jsonl(args.ambig_inputs))
    disambig_rows = dedup(read_jsonl(args.disambig_inputs))

    summary_rows = summarize_ambig(ambig_rows) + summarize_disambig(disambig_rows)
    write_csv(Path(args.output_csv), summary_rows)
    write_md(Path(args.output_md), summary_rows)
    print(f"Wrote {len(summary_rows)} summary rows")
    print(f"CSV: {args.output_csv}")
    print(f"MD: {args.output_md}")


if __name__ == "__main__":
    main()
