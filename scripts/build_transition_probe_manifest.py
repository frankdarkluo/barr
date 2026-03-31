import argparse
from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from barr.io_utils import write_jsonl
from barr.transition_probe import load_bbq_ambiguous_records, stratified_sample_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root", default="data")
    parser.add_argument("--context_condition", default="ambig")
    parser.add_argument("--total_samples", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        default="outputs/transition_probe/sample_manifest/bbq_ambig_200.jsonl",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    grouped = load_bbq_ambiguous_records(data_root=args.data_root, context_condition=args.context_condition)
    rows = stratified_sample_records(grouped, total_samples=args.total_samples, seed=args.seed)

    output_path = Path(args.output)
    write_jsonl(output_path, rows)

    counts = Counter(row["category"] for row in rows)
    print(f"Saved {len(rows)} rows to {output_path}")
    for category, count in sorted(counts.items()):
        print(f"{category}: {count}")


if __name__ == "__main__":
    main()
