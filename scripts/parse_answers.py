#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from barr.config import load_yaml
from barr.io_utils import read_jsonl, write_csv
from barr.reasoning import answer_parse_success, parse_model_output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/week1_pilot.yaml")
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    config = load_yaml(args.config)
    rows = []
    for input_path in args.inputs:
        for row in read_jsonl(Path(input_path)):
            reasoning_text, final_answer = parse_model_output(row.get("raw_output", ""))
            rows.append(
                {
                    "sample_id": row["sample_id"],
                    "model_name": row["model_name"],
                    "quant_method": row["quant_method"],
                    "dataset_name": row["dataset_name"],
                    "language": row["language"],
                    "final_answer": final_answer,
                    "parse_success": answer_parse_success(row.get("raw_output", "")),
                    "reasoning_text_matches_saved": reasoning_text == row.get("reasoning_text", ""),
                }
            )

    output_path = Path(config["paths"]["parse_answers_path"])
    write_csv(
        output_path,
        rows,
        fieldnames=[
            "sample_id",
            "model_name",
            "quant_method",
            "dataset_name",
            "language",
            "final_answer",
            "parse_success",
            "reasoning_text_matches_saved",
        ],
    )
    print(f"Wrote parse validation to {output_path}")


if __name__ == "__main__":
    main()

