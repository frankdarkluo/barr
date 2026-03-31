import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from barr.transition_probe import is_transition_token_text, transition_term_set


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model_name_or_path", required=True)
    parser.add_argument("--cache_dir", default="/home/gluo/models")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line.startswith("{"):
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        cache_dir=args.cache_dir,
        trust_remote_code=True,
    )
    allowed_terms = transition_term_set()
    rows = read_jsonl(Path(args.input))
    if args.limit is not None:
        rows = rows[: args.limit]

    output_path = Path(args.output)
    if output_path.exists():
        output_path.unlink()

    for idx, row in enumerate(rows, start=1):
        response = row.get("response", "")
        token_ids = tokenizer(response, return_tensors="pt", add_special_tokens=False)["input_ids"][0].tolist()
        transition_points = []
        for token_index, token_id in enumerate(token_ids):
            token_text = tokenizer.decode([token_id], skip_special_tokens=False)
            if is_transition_token_text(token_text, allowed_terms=allowed_terms):
                transition_points.append(
                    {
                        "k": len(transition_points) + 1,
                        "token_index": token_index,
                        "token_id": token_id,
                        "token_text": token_text,
                    }
                )

        enriched = dict(row)
        enriched["transition_points_text"] = transition_points
        append_jsonl(output_path, enriched)
        print(
            json.dumps(
                {
                    "completed": idx,
                    "sample_id": row.get("sample_id"),
                    "transition_count": len(transition_points),
                },
                ensure_ascii=False,
            )
        )

    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
