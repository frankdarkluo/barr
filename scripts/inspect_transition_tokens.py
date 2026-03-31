import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from barr.io_utils import ensure_parent
from barr.transition_probe import TRANSITION_TERMS, normalize_transition_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", default="Qwen/Qwen3-8B")
    parser.add_argument("--cache_dir", default="/home/gluo/models")
    parser.add_argument(
        "--output",
        default="outputs/transition_probe/analysis/transition_token_map.json",
    )
    return parser.parse_args()


def inspect_term(tokenizer, term: str) -> dict:
    variants = [term, f" {term}", f"\n{term}", term.lower(), f" {term.lower()}"]
    inspected = []
    single_token_surfaces = set()
    single_token_ids = set()
    for variant in variants:
        token_ids = tokenizer.encode(variant, add_special_tokens=False)
        decoded_tokens = [tokenizer.decode([token_id], skip_special_tokens=False) for token_id in token_ids]
        inspected.append(
            {
                "variant": variant,
                "token_ids": token_ids,
                "decoded_tokens": decoded_tokens,
            }
        )
        if len(token_ids) == 1:
            single_token_ids.add(token_ids[0])
            single_token_surfaces.add(normalize_transition_text(decoded_tokens[0]))
    return {
        "term": term,
        "normalized_term": term.lower(),
        "variants": inspected,
        "single_token_ids": sorted(single_token_ids),
        "single_token_surfaces": sorted(surface for surface in single_token_surfaces if surface),
    }


def main() -> None:
    args = parse_args()
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        cache_dir=args.cache_dir,
        trust_remote_code=True,
    )

    report = {
        "model_name_or_path": args.model_name_or_path,
        "terms": [inspect_term(tokenizer, term) for term in TRANSITION_TERMS],
        "recommended_surface_whitelist": sorted(term.lower() for term in TRANSITION_TERMS),
    }

    output_path = Path(args.output)
    ensure_parent(output_path)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved transition token report to {output_path}")


if __name__ == "__main__":
    main()
