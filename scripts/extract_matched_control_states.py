import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", default="Qwen/Qwen3-8B")
    parser.add_argument("--cache_dir", default="/home/gluo/models")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--tensor_dir", required=True)
    parser.add_argument("--device", default=None)
    parser.add_argument("--radius", type=int, default=5)
    parser.add_argument("--save_last_n_layers", type=int, default=4)
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


def deterministic_rng(sample_id: str, seed: int) -> np.random.Generator:
    digest = hashlib.sha256(f"{sample_id}:{seed}".encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return np.random.default_rng(value)


def choose_control_index(
    generated_tokens: int,
    first_transition_index: int,
    transition_indices: set[int],
    sample_id: str,
    seed: int,
    radius: int,
) -> int | None:
    start = max(0, first_transition_index - radius)
    end = min(generated_tokens - 1, first_transition_index + radius)
    candidates = [
        idx
        for idx in range(start, end + 1)
        if idx != first_transition_index and idx not in transition_indices
    ]
    if not candidates:
        return None
    rng = deterministic_rng(sample_id, seed)
    return int(rng.choice(np.asarray(candidates, dtype=np.int64)))


def save_tensor_from_position(
    path: Path,
    hidden_states,
    full_position: int,
    last_n_layers: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {}
    for layer_offset in range(1, last_n_layers + 1):
        layer_name = f"layer_-{layer_offset}"
        payload[layer_name] = (
            hidden_states[-layer_offset][:, full_position, :].detach().cpu().to(torch.float32)
        )
    torch.save(payload, path)


def cosine(a: torch.Tensor, b: torch.Tensor) -> float:
    a = a.reshape(-1).to(torch.float32)
    b = b.reshape(-1).to(torch.float32)
    denom = torch.linalg.vector_norm(a) * torch.linalg.vector_norm(b)
    if float(denom) == 0.0:
        return 0.0
    return float(torch.dot(a, b) / denom)


def resolve_position_mode(
    hidden_states,
    prompt_len: int,
    transition_index: int,
    saved_transition_tensor_path: Path,
) -> tuple[int | None, float | None]:
    if not saved_transition_tensor_path.exists():
        return None, None
    saved = torch.load(saved_transition_tensor_path, map_location="cpu")["layer_-1"]

    candidates = []
    for delta in (-1, 0):
        full_position = prompt_len + transition_index + delta
        if full_position < 0 or full_position >= hidden_states[-1].shape[1]:
            continue
        current = hidden_states[-1][:, full_position, :].detach().cpu()
        score = cosine(current, saved)
        candidates.append((delta, score))

    if not candidates:
        return None, None
    best_delta, best_score = max(candidates, key=lambda item: item[1])
    return int(best_delta), float(best_score)


def main() -> None:
    args = parse_args()

    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        cache_dir=args.cache_dir,
        trust_remote_code=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        cache_dir=args.cache_dir,
        trust_remote_code=True,
        dtype=torch.bfloat16,
    )
    target_device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(target_device)
    model.eval()

    rows = read_jsonl(Path(args.input))
    if args.limit is not None:
        rows = rows[: args.limit]

    output_path = Path(args.output)
    if output_path.exists():
        output_path.unlink()

    for idx, row in enumerate(rows, start=1):
        label = row.get("trajectory_label")
        transitions = row.get("transition_points") or []
        control_meta = None
        if label in {"correct", "biased"} and transitions:
            prompt_ids = tokenizer(row["prompt"], return_tensors="pt", add_special_tokens=False)["input_ids"]
            response_ids = tokenizer(row["response"], return_tensors="pt", add_special_tokens=False)["input_ids"]
            prompt_len = int(prompt_ids.shape[1])
            response_len = int(response_ids.shape[1])
            full_ids = torch.cat([prompt_ids, response_ids], dim=1).to(model.device)
            attention_mask = torch.ones_like(full_ids, device=model.device)

            with torch.no_grad():
                outputs = model(
                    input_ids=full_ids,
                    attention_mask=attention_mask,
                    output_hidden_states=True,
                    return_dict=True,
                )

            first_transition = transitions[0]
            position_mode, transition_cos = resolve_position_mode(
                hidden_states=outputs.hidden_states,
                prompt_len=prompt_len,
                transition_index=int(first_transition["token_index"]),
                saved_transition_tensor_path=Path(first_transition["tensor_path"]),
            )

            transition_indices = {int(point["token_index"]) for point in transitions}
            control_index = choose_control_index(
                generated_tokens=response_len,
                first_transition_index=int(first_transition["token_index"]),
                transition_indices=transition_indices,
                sample_id=row["sample_id"],
                seed=int(row["seed"]),
                radius=args.radius,
            )

            if position_mode is not None and control_index is not None:
                full_position = prompt_len + control_index + position_mode
                if 0 <= full_position < outputs.hidden_states[-1].shape[1]:
                    control_tensor_path = (
                        Path(args.tensor_dir)
                        / f"{row['sample_id'].replace(':', '_')}_seed{row['seed']}_control.pt"
                    )
                    save_tensor_from_position(
                        path=control_tensor_path,
                        hidden_states=outputs.hidden_states,
                        full_position=full_position,
                        last_n_layers=args.save_last_n_layers,
                    )
                    token_text = tokenizer.decode(
                        response_ids[0, control_index : control_index + 1].tolist(),
                        skip_special_tokens=False,
                    )
                    control_meta = {
                        "token_index": int(control_index),
                        "full_position": int(full_position),
                        "token_text": token_text,
                        "tensor_path": str(control_tensor_path),
                        "distance_from_first_transition": int(control_index - int(first_transition["token_index"])),
                        "response_token_count": response_len,
                        "transition_alignment_delta": int(position_mode),
                        "transition_alignment_cosine": float(transition_cos) if transition_cos is not None else None,
                    }

        out_row = dict(row)
        out_row["matched_control_point"] = control_meta
        append_jsonl(output_path, out_row)
        print(
            json.dumps(
                {
                    "completed": idx,
                    "sample_id": row["sample_id"],
                    "has_control": control_meta is not None,
                },
                ensure_ascii=False,
            )
        )

    print(f"Saved matched control rows to {output_path}")


if __name__ == "__main__":
    main()
