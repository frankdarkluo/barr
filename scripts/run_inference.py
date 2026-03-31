#!/usr/bin/env python
import argparse
import re
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from barr.config import load_yaml
from barr.datasets import simple_tokenize
from barr.io_utils import read_jsonl, write_jsonl
from barr.reasoning import answer_parse_success, parse_model_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/week1_pilot.yaml")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--quant-method", required=True)
    parser.add_argument("--dataset-name", required=True, choices=["mbbq", "openmbbq"])
    parser.add_argument("--language", required=True, choices=["english", "chinese", "urdu"])
    parser.add_argument("--output-path")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--backend",
        default="vllm",
        choices=["vllm", "dummy"],
        help="Use dummy for local smoke tests when vLLM is unavailable.",
    )
    return parser.parse_args()


def iter_manifest_rows(manifest_path: Path, dataset_name: str, language: str, limit: Optional[int]) -> List[Dict]:
    rows = [
        row
        for row in read_jsonl(manifest_path)
        if row["dataset_name"] == dataset_name and row["language"] == language
    ]
    rows.sort(key=lambda row: row["sample_id"])
    if limit is not None:
        rows = rows[:limit]
    return rows


def slugify_model_name(model_name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", model_name.strip())
    slug = slug.strip("-")
    return slug or "model"


def dummy_generate(prompts: Iterable[str]) -> List[str]:
    outputs = []
    for prompt in prompts:
        outputs.append(
            "<think>I should only use the provided context. The safe choice is the unknown option when the context is ambiguous.</think>\n"
            "<answer>C</answer>"
        )
    return outputs


def vllm_generate(
    prompts: List[str],
    model_name: str,
    config: Dict,
) -> List[Dict]:
    try:
        from vllm import LLM, SamplingParams
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "vLLM is not installed in this environment. Re-run with --backend dummy for a smoke test "
            "or install vllm before launching real inference."
        ) from exc

    sampling_cfg = config["inference"]
    llm = LLM(
        model=model_name,
        download_dir=sampling_cfg["cache_dir"],
        tensor_parallel_size=sampling_cfg.get("tensor_parallel_size", 1),
        trust_remote_code=True,
    )
    params = SamplingParams(
        temperature=sampling_cfg["temperature"],
        top_p=sampling_cfg["top_p"],
        max_tokens=sampling_cfg["max_new_tokens"],
        seed=sampling_cfg["seed"],
    )
    tokenizer = llm.get_tokenizer()
    generations = llm.generate(prompts, sampling_params=params, use_tqdm=True)
    rows = []
    for generation in generations:
        output = generation.outputs[0]
        prompt_token_ids = tokenizer.encode(generation.prompt)
        rows.append(
            {
                "text": output.text,
                "prompt_tokens": len(prompt_token_ids),
                "total_tokens": len(output.token_ids),
                "generated_tokens": len(output.token_ids),
                "logprobs_available": False,
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    config = load_yaml(args.config)
    manifest_path = Path(config["paths"]["manifest_path"])
    rows = iter_manifest_rows(manifest_path, args.dataset_name, args.language, args.limit)
    if not rows:
        raise SystemExit("No manifest rows matched the requested dataset/language filter.")

    model_slug = slugify_model_name(args.model_name)
    output_path = Path(
        args.output_path
        or f"outputs/{model_slug}/{args.dataset_name}/{args.language}.jsonl"
    )

    prompts = [row["prompt"] for row in rows]
    started = time.perf_counter()
    if args.backend == "dummy":
        raw_outputs = [
            {
                "text": text,
                "prompt_tokens": len(simple_tokenize(prompt)),
                "generated_tokens": len(simple_tokenize(text)),
                "total_tokens": len(simple_tokenize(prompt)) + len(simple_tokenize(text)),
                "logprobs_available": False,
            }
            for prompt, text in zip(prompts, dummy_generate(prompts))
        ]
    else:
        raw_outputs = vllm_generate(prompts=prompts, model_name=args.model_name, config=config)
    total_runtime = time.perf_counter() - started

    results = []
    per_sample_latency = total_runtime / max(len(rows), 1)
    for row, output in zip(rows, raw_outputs):
        reasoning_text, final_answer = parse_model_output(output["text"])
        think_tokens = len(simple_tokenize(reasoning_text))
        results.append(
            {
                **row,
                "model_name": args.model_name,
                "quant_method": args.quant_method,
                "dataset": row["dataset_name"],
                "quantization": args.quant_method,
                "protected_attribute_category": row["category"],
                "raw_output": output["text"],
                "reasoning_text": reasoning_text,
                "final_answer": final_answer,
                "parse_success": answer_parse_success(output["text"]),
                "accuracy_label": row["label_letter"],
                "stereotype_label": row.get("bias_target_letter"),
                "unknown_label": row.get("unknown_letter"),
                "prompt_tokens": output.get("prompt_tokens"),
                "generated_tokens": output.get("generated_tokens", output["total_tokens"]),
                "total_tokens": output["total_tokens"],
                "think_tokens": think_tokens,
                "latency": per_sample_latency,
                "logprobs_available": output.get("logprobs_available", False),
            }
        )

    write_jsonl(output_path, results)
    print(f"Wrote {len(results)} inference rows to {output_path}")


if __name__ == "__main__":
    main()
