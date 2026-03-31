#!/usr/bin/env python
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from barr.config import load_yaml
from barr.datasets import build_manifest_rows, load_ambiguous_records
from barr.io_utils import write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/week1_pilot.yaml")
    args = parser.parse_args()

    config = load_yaml(args.config)
    manifest_path = Path(config["paths"]["manifest_path"])
    records = load_ambiguous_records(data_root=config["paths"]["data_root"])
    manifest_rows = build_manifest_rows(
        records=records,
        sample_size_per_language=config["experiment"]["sample_size_per_language"],
        seed=config["experiment"]["seed"],
        dataset_names=config["experiment"]["dataset_names"],
    )
    write_jsonl(manifest_path, manifest_rows)
    print(f"Wrote {len(manifest_rows)} rows to {manifest_path}")


if __name__ == "__main__":
    main()
