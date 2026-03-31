#!/usr/bin/env python
import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from barr.transition_probe import (  # noqa: E402
    classify_trajectory,
    format_chat_prompt,
    is_transition_token_text,
    transition_term_set,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model_name_or_path", default="Qwen/Qwen3-8B-AWQ")
    parser.add_argument("--cache_dir", default="/home/gluo/models")
    parser.add_argument("--seed", type=int, default=0)
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


def classify_for_context(answer_id: str, question: dict, correct_answer_id: str) -> str:
    context_condition = question.get("context_condition", "ambig")
    if context_condition == "disambig":
        if not answer_id:
            return "unparsed"
        if answer_id == correct_answer_id:
            return "correct"
        if answer_id == question.get("bias_target"):
            return "biased"
        return "counter_biased"
    return classify_trajectory(answer_id, question)


def main() -> None:
    args = parse_args()

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        cache_dir=args.cache_dir,
        trust_remote_code=True,
    )

    rows = read_jsonl(Path(args.input))
    if args.limit is not None:
        rows = rows[: args.limit]

    output_path = Path(args.output)
    if output_path.exists():
        output_path.unlink()

    allowed_terms = transition_term_set()
    for idx, row in enumerate(rows, start=1):
        question = row["question"]
        correct_answer_id = row.get("correct_answer_id") or f"ans{question['label']}"

        prompt_record = {
            "context": question["context"],
            "question": question["question"],
            "ans0": question["ans0"],
            "ans1": question["ans1"],
            "ans2": question["ans2"],
        }
        prompt_text = format_chat_prompt(
            tokenizer=tokenizer,
            record=prompt_record,
            model_name=args.model_name_or_path,
            force_think=True,
        )

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

        trajectory_label = classify_for_context(
            answer_id=row.get("answer", ""),
            question=question,
            correct_answer_id=correct_answer_id,
        )

        out_row = {
            "sample_id": str(row.get("sample_id", question.get("example_id", idx))),
            "seed": args.seed,
            "category": row.get("category", question.get("category", "age")),
            "prompt": prompt_text,
            "response": response,
            "answer": row.get("answer", ""),
            "answer_text": row.get("answer_text", ""),
            "trajectory_label": trajectory_label,
            "generated_tokens": int(row.get("generated_tokens", 0)),
            "question": question,
            "correct_answer_id": correct_answer_id,
        }
        if transition_points:
            out_row["transition_points"] = transition_points

        append_jsonl(output_path, out_row)

        if idx % 200 == 0:
            print(json.dumps({"processed": idx, "last_sample_id": out_row["sample_id"]}, ensure_ascii=False))

    print(f"Saved {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
