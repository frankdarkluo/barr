import argparse
import json
import time
from pathlib import Path
import sys

import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from barr.io_utils import ensure_parent, read_jsonl, write_jsonl
from barr.transition_probe import (
    classify_trajectory,
    extract_reasoning_and_answer,
    format_chat_prompt,
    map_answer_text_to_id,
    transition_term_set,
    is_transition_token_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", default="Qwen/Qwen3-8B")
    parser.add_argument("--cache_dir", default="/home/gluo/models")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--tensor_dir", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", default=None)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--max_new_tokens", type=int, default=2048)
    parser.add_argument("--save_last_n_layers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None)
    parser.set_defaults(force_think=True)
    parser.add_argument("--force_think", dest="force_think", action="store_true")
    parser.add_argument("--no_force_think", dest="force_think", action="store_false")
    parser.add_argument("--save_attentions", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def sample_next_token(logits: torch.Tensor, temperature: float, top_p: float) -> torch.Tensor:
    if temperature <= 0:
        return torch.argmax(logits, dim=-1, keepdim=True)

    scaled = logits / temperature
    probs = torch.softmax(scaled, dim=-1)
    sorted_probs, sorted_indices = torch.sort(probs, descending=True)
    cumulative = torch.cumsum(sorted_probs, dim=-1)
    cutoff = cumulative > top_p
    cutoff[..., 1:] = cutoff[..., :-1].clone()
    cutoff[..., 0] = False
    sorted_probs = sorted_probs.masked_fill(cutoff, 0)
    sorted_probs = sorted_probs / sorted_probs.sum(dim=-1, keepdim=True)
    sampled = torch.multinomial(sorted_probs, num_samples=1)
    return torch.gather(sorted_indices, -1, sampled)


def save_transition_tensor(path: Path, hidden_states, last_n_layers: int) -> None:
    ensure_parent(path)
    payload = {}
    for layer_offset in range(1, last_n_layers + 1):
        layer_name = f"layer_-{layer_offset}"
        payload[layer_name] = hidden_states[-layer_offset][:, -1, :].detach().cpu().to(torch.float32)
    torch.save(payload, path)


def append_jsonl_row(path: Path, row: dict) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)

    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        cache_dir=args.cache_dir,
        trust_remote_code=True,
    )
    load_kwargs = {
        "cache_dir": args.cache_dir,
        "trust_remote_code": True,
        "dtype": torch.bfloat16,
    }
    requested_device = args.device
    try:
        if requested_device:
            raise ValueError("skip_device_map_auto")
        model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path, device_map="auto", **load_kwargs)
    except ValueError as exc:
        if "requires `accelerate`" not in str(exc) and "skip_device_map_auto" not in str(exc):
            raise
        model = AutoModelForCausalLM.from_pretrained(
            args.model_name_or_path,
            **load_kwargs,
        )
        target_device = requested_device or ("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(target_device)
    model.eval()

    manifest_rows = list(read_jsonl(Path(args.manifest)))
    if args.limit is not None:
        manifest_rows = manifest_rows[: args.limit]

    output_path = Path(args.output) if args.output else Path(f"outputs/transition_probe/raw/seed_{args.seed}.jsonl")
    tensor_dir = Path(args.tensor_dir) if args.tensor_dir else output_path.parent / "tensors"
    allowed_terms = transition_term_set()
    existing_rows = []
    completed_ids = set()
    if args.resume and output_path.exists():
        existing_rows = list(read_jsonl(output_path))
        completed_ids = {row["sample_id"] for row in existing_rows}
        print(f"Resuming from {output_path} with {len(existing_rows)} completed rows")

    rows = list(existing_rows)
    pending_rows = [row for row in manifest_rows if row["sample_id"] not in completed_ids]
    for index, row in enumerate(pending_rows, start=1):
        prompt = format_chat_prompt(tokenizer, row, args.model_name_or_path, force_think=args.force_think)
        encoded = tokenizer(prompt, return_tensors="pt")
        input_ids = encoded["input_ids"].to(model.device)
        attention_mask = encoded["attention_mask"].to(model.device)

        generated_ids = []
        generated_pieces = []
        transition_points = []
        past_key_values = None
        current_ids = input_ids
        current_mask = attention_mask
        started = time.perf_counter()

        with torch.no_grad():
            for step in range(args.max_new_tokens):
                outputs = model(
                    input_ids=current_ids,
                    attention_mask=current_mask,
                    past_key_values=past_key_values,
                    use_cache=True,
                    output_hidden_states=True,
                    output_attentions=args.save_attentions,
                    return_dict=True,
                )
                next_token = sample_next_token(outputs.logits[:, -1, :], args.temperature, args.top_p)
                token_id = int(next_token.item())
                token_text = tokenizer.decode([token_id], skip_special_tokens=False)

                if is_transition_token_text(token_text, allowed_terms=allowed_terms):
                    tensor_path = tensor_dir / f"{row['sample_id'].replace(':', '_')}_seed{args.seed}_k{len(transition_points)+1}.pt"
                    save_transition_tensor(tensor_path, outputs.hidden_states, args.save_last_n_layers)
                    transition_points.append(
                        {
                            "k": len(transition_points) + 1,
                            "token_index": len(generated_ids),
                            "token_id": token_id,
                            "token_text": token_text,
                            "tensor_path": str(tensor_path),
                        }
                    )

                generated_ids.append(token_id)
                generated_pieces.append(token_text)
                if tokenizer.eos_token_id is not None and token_id == tokenizer.eos_token_id:
                    break
                if "</answer>" in "".join(generated_pieces).lower():
                    break

                current_ids = next_token.to(model.device)
                attention_mask = torch.cat(
                    [attention_mask, torch.ones((attention_mask.shape[0], 1), dtype=attention_mask.dtype, device=model.device)],
                    dim=1,
                )
                current_mask = attention_mask
                past_key_values = outputs.past_key_values

        latency = time.perf_counter() - started
        response = tokenizer.decode(generated_ids, skip_special_tokens=True)
        parsed = extract_reasoning_and_answer(response)
        answer_id = map_answer_text_to_id(parsed["answer_text"], row) if parsed["parse_success"] else ""
        trajectory_label = classify_trajectory(answer_id, row)

        result_row = {
            "sample_id": row["sample_id"],
            "seed": args.seed,
            "category": row["category"],
            "context_condition": row["context_condition"],
            "prompt": prompt,
            "response": response,
            "reasoning_text": parsed["reasoning_text"],
            "answer": answer_id,
            "answer_text": parsed["answer_text"],
            "parse_success": parsed["parse_success"],
            "correct_answer_id": row["unknown_id"],
            "trajectory_label": trajectory_label,
            "transition_points": transition_points,
            "generated_tokens": len(generated_ids),
            "latency_sec": round(latency, 4),
            "question": row,
        }
        rows.append(result_row)
        append_jsonl_row(output_path, result_row)
        print(
            json.dumps(
                {
                    "completed": len(rows),
                    "pending_index": index,
                    "current_sample_id": row["sample_id"],
                    "parse_success": parsed["parse_success"],
                    "trajectory_label": trajectory_label,
                    "transition_count": len(transition_points),
                    "generated_tokens": len(generated_ids),
                },
                ensure_ascii=False,
            )
        )
    summary = {
        "rows": len(rows),
        "with_transition": sum(1 for row in rows if row["transition_points"]),
        "biased": sum(1 for row in rows if row["trajectory_label"] == "biased"),
        "correct": sum(1 for row in rows if row["trajectory_label"] == "correct"),
        "counter_biased": sum(1 for row in rows if row["trajectory_label"] == "counter_biased"),
        "unparsed": sum(1 for row in rows if row["trajectory_label"] == "unparsed"),
    }
    print(f"Saved transition probe rows to {output_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
