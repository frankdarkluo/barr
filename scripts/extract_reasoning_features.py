#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from barr.config import load_yaml
from barr.io_utils import read_jsonl, write_csv
from barr.reasoning import extract_reasoning_features


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/week1_pilot.yaml")
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    rows = []
    for input_path in args.inputs:
        for row in read_jsonl(Path(input_path)):
            features = extract_reasoning_features(row)
            rows.append(
                {
                    "sample_id": row["sample_id"],
                    "model_name": row["model_name"],
                    "quant_method": row["quant_method"],
                    "dataset_name": row["dataset_name"],
                    "language": row["language"],
                    "category": row["category"],
                    **features,
                }
            )

    output_path = Path(config["paths"]["reasoning_features_path"])
    write_csv(
        output_path,
        rows,
        fieldnames=[
            "sample_id",
            "model_name",
            "quant_method",
            "dataset_name",
            "language",
            "category",
            "reasoning_length",
            "transition_marker_count",
            "unsupported_attribute_mention_count",
            "unsupported_attribute_mention_rate",
            "stereotype_lexicon_hit_count",
            "repeated_stereotype_span_count",
            "irrelevant_information_proxy_count",
        ],
    )
    print(f"Wrote reasoning features to {output_path}")


if __name__ == "__main__":
    main()
