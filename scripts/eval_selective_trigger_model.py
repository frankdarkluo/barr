#!/usr/bin/env python
import argparse
import csv
import glob
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


TRANSITION_PATTERN = re.compile(r"\b(Wait|Alternatively|Hmm|But|but)\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ambig-input", required=True)
    parser.add_argument("--disambig-input", required=True)
    parser.add_argument("--ambig-eval-glob", required=True)
    parser.add_argument("--disambig-eval-glob", required=True)
    parser.add_argument("--condition", default="redirect")
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--target-trigger-min", type=float, default=0.10)
    parser.add_argument("--target-trigger-max", type=float, default=0.20)
    parser.add_argument("--harm-budget", type=float, default=0.05)
    return parser.parse_args()


def read_jsonl(path: str) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("{"):
                rows.append(json.loads(line))
    return rows


def read_glob_jsonl(pattern: str) -> list[dict]:
    rows = []
    for path in sorted(glob.glob(pattern)):
        rows.extend(read_jsonl(path))
    return rows


def dedup_eval_rows(rows: list[dict]) -> dict[tuple[str, str], dict]:
    seen = {}
    for row in rows:
        key = (str(row["sample_id"]), row["condition"])
        if key not in seen:
            seen[key] = row
    return seen


def normalize_token_text(text: str) -> str:
    return (text or "").strip().lower() or "none"


def prefix_text(response: str, has_transition: bool) -> str:
    # Strict-online rule: if no transition is observed, do not use the trajectory text.
    if not has_transition:
        return ""

    match = TRANSITION_PATTERN.search(response or "")
    if not match:
        return ""
    return response[: match.start()]


def to_label_tokens(row: dict | None) -> dict:
    if not row:
        return {"label": "unparsed", "tokens": 0}
    return {
        "label": row.get("trajectory_label", "unparsed"),
        "tokens": int(row.get("generated_tokens", 0)),
    }


def build_frame(rows: list[dict], split_name: str) -> pd.DataFrame:
    records = []
    for row in rows:
        response = row.get("response", "")
        transition_points = row.get("transition_points") or []
        has_transition = len(transition_points) > 0
        pref = prefix_text(response, has_transition=has_transition)
        first_idx = int(transition_points[0]["token_index"]) if has_transition else -1
        first_token = normalize_token_text(transition_points[0]["token_text"]) if has_transition else "none"
        prefix_words = len(pref.split())
        label = row.get("trajectory_label", "unparsed")
        records.append(
            {
                "sample_id": str(row["sample_id"]),
                "group_id": f"{split_name}:{row['sample_id']}",
                "split": split_name,
                "trajectory_label": label,
                "vanilla_correct": int(label == "correct"),
                "risk_positive": int(label != "correct"),
                "ambig_biased": int(split_name == "ambig" and label == "biased"),
                "disambig_correct": int(split_name == "disambig" and label == "correct"),
                "has_transition": int(has_transition),
                "first_transition_index": first_idx,
                "first_transition_token": first_token,
                "prefix_text": pref,
                "prefix_word_count": prefix_words,
                "prefix_char_count": len(pref),
            }
        )
    return pd.DataFrame.from_records(records)


def build_outcome_map(
    eval_rows: dict[tuple[str, str], dict],
    condition: str,
    split_name: str,
) -> dict[str, dict]:
    out = {}
    sample_ids = {sid for sid, _ in eval_rows.keys()}
    for sample_id in sample_ids:
        vanilla = eval_rows[(sample_id, "vanilla")]
        intervention = eval_rows[(sample_id, condition)]
        always_reflect = eval_rows.get((sample_id, "always_reflect"))
        out[f"{split_name}:{sample_id}"] = {
            "vanilla": to_label_tokens(vanilla),
            "intervention": to_label_tokens(intervention),
            "always_reflect": to_label_tokens(always_reflect) if always_reflect else to_label_tokens(vanilla),
        }
    return out


def split_ids(frame: pd.DataFrame, random_seed: int) -> tuple[set[str], set[str], set[str]]:
    group_df = frame[["group_id", "risk_positive"]].drop_duplicates()
    ids = group_df["group_id"].astype(str).tolist()
    labels = group_df["risk_positive"].astype(int).tolist()

    train_ids, temp_ids, train_y, temp_y = train_test_split(
        ids,
        labels,
        test_size=0.4,
        random_state=random_seed,
        stratify=labels,
    )
    dev_ids, test_ids = train_test_split(
        temp_ids,
        test_size=0.5,
        random_state=random_seed,
        stratify=temp_y,
    )
    return set(train_ids), set(dev_ids), set(test_ids)


def build_models(random_seed: int) -> dict[str, Pipeline]:
    numeric_features = [
        "has_transition",
        "first_transition_index",
        "prefix_word_count",
        "prefix_char_count",
    ]

    text_model = Pipeline(
        steps=[
            (
                "features",
                ColumnTransformer(
                    transformers=[
                        ("num", StandardScaler(), numeric_features),
                        (
                            "tok",
                            OneHotEncoder(handle_unknown="ignore"),
                            ["first_transition_token"],
                        ),
                        (
                            "txt",
                            TfidfVectorizer(max_features=300, ngram_range=(1, 2), min_df=2),
                            "prefix_text",
                        ),
                    ]
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                    random_state=random_seed,
                ),
            ),
        ]
    )

    position_model = Pipeline(
        steps=[
            (
                "features",
                ColumnTransformer(
                    transformers=[
                        ("num", StandardScaler(), ["first_transition_index"]),
                    ]
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=random_seed,
                ),
            ),
        ]
    )
    return {
        "position_only_lr": position_model,
        "text_level_lr": text_model,
    }


def evaluate_policy(
    frame: pd.DataFrame,
    outcomes: dict[str, dict],
    scores: dict[str, float],
    threshold: float,
) -> dict:
    trigger_count = 0
    ambig_biased_base = 0
    ambig_corrected = 0
    disambig_correct_base = 0
    disambig_harmed = 0
    total_generated_tokens = 0
    total_vanilla_tokens = 0

    for row in frame.to_dict("records"):
        group_id = row["group_id"]
        has_transition = bool(row["has_transition"])
        triggered = has_transition and (scores[group_id] >= threshold)
        if triggered:
            trigger_count += 1

        policy_key = "intervention" if triggered else "vanilla"
        final = outcomes[group_id][policy_key]
        final_label = final["label"]
        total_generated_tokens += final["tokens"]
        total_vanilla_tokens += outcomes[group_id]["vanilla"]["tokens"]

        if row["ambig_biased"]:
            ambig_biased_base += 1
            if final_label == "correct":
                ambig_corrected += 1

        if row["disambig_correct"]:
            disambig_correct_base += 1
            if final_label != "correct":
                disambig_harmed += 1

    return {
        "threshold": float(threshold),
        "trigger_count": trigger_count,
        "trigger_rate": trigger_count / max(len(frame), 1),
        "ambig_biased_base": ambig_biased_base,
        "ambig_corrected": ambig_corrected,
        "ambig_correction_rate": ambig_corrected / max(ambig_biased_base, 1),
        "disambig_correct_base": disambig_correct_base,
        "disambig_harmed": disambig_harmed,
        "disambig_harm_rate": disambig_harmed / max(disambig_correct_base, 1),
        "net_benefit": ambig_corrected - disambig_harmed,
        "total_generated_tokens": total_generated_tokens,
        "avg_generated_tokens": total_generated_tokens / max(len(frame), 1),
        "total_token_delta_vs_vanilla": total_generated_tokens - total_vanilla_tokens,
        "avg_token_delta_vs_vanilla": (total_generated_tokens - total_vanilla_tokens) / max(len(frame), 1),
    }


def threshold_sweep(
    frame: pd.DataFrame,
    outcomes: dict[str, dict],
    scores: dict[str, float],
) -> list[dict]:
    thresholds = sorted(
        {
            scores[row["group_id"]]
            for row in frame.to_dict("records")
            if row["has_transition"]
        }
    )
    if not thresholds:
        thresholds = [1.0]
    return [evaluate_policy(frame, outcomes, scores, threshold) for threshold in thresholds]


def choose_threshold(
    sweep_rows: list[dict],
    target_trigger_min: float,
    target_trigger_max: float,
    harm_budget: float,
) -> dict:
    constrained = [row for row in sweep_rows if row["disambig_harm_rate"] <= harm_budget]
    in_band = [
        row
        for row in constrained
        if target_trigger_min <= row["trigger_rate"] <= target_trigger_max
    ]
    pool = in_band or constrained or sweep_rows
    return max(
        pool,
        key=lambda row: (row["net_benefit"], row["ambig_correction_rate"], -row["disambig_harm_rate"]),
    )


def baseline_metrics(frame: pd.DataFrame, outcomes: dict[str, dict], condition_key: str) -> dict:
    ambig_biased_base = 0
    ambig_corrected = 0
    disambig_correct_base = 0
    disambig_harmed = 0
    total_generated_tokens = 0
    total_vanilla_tokens = 0
    for row in frame.to_dict("records"):
        group_id = row["group_id"]
        final = outcomes[group_id][condition_key]
        final_label = final["label"]
        total_generated_tokens += final["tokens"]
        total_vanilla_tokens += outcomes[group_id]["vanilla"]["tokens"]
        if row["ambig_biased"]:
            ambig_biased_base += 1
            if final_label == "correct":
                ambig_corrected += 1
        if row["disambig_correct"]:
            disambig_correct_base += 1
            if final_label != "correct":
                disambig_harmed += 1
    return {
        "trigger_rate": 1.0 if condition_key != "vanilla" else 0.0,
        "ambig_biased_base": ambig_biased_base,
        "ambig_corrected": ambig_corrected,
        "ambig_correction_rate": ambig_corrected / max(ambig_biased_base, 1),
        "disambig_correct_base": disambig_correct_base,
        "disambig_harmed": disambig_harmed,
        "disambig_harm_rate": disambig_harmed / max(disambig_correct_base, 1),
        "net_benefit": ambig_corrected - disambig_harmed,
        "total_generated_tokens": total_generated_tokens,
        "avg_generated_tokens": total_generated_tokens / max(len(frame), 1),
        "total_token_delta_vs_vanilla": total_generated_tokens - total_vanilla_tokens,
        "avg_token_delta_vs_vanilla": (total_generated_tokens - total_vanilla_tokens) / max(len(frame), 1),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()

    ambig_frame = build_frame(read_jsonl(args.ambig_input), "ambig")
    disambig_frame = build_frame(read_jsonl(args.disambig_input), "disambig")
    frame = pd.concat([ambig_frame, disambig_frame], ignore_index=True)

    ambig_outcomes = build_outcome_map(
        dedup_eval_rows(read_glob_jsonl(args.ambig_eval_glob)),
        args.condition,
        split_name="ambig",
    )
    disambig_outcomes = build_outcome_map(
        dedup_eval_rows(read_glob_jsonl(args.disambig_eval_glob)),
        args.condition,
        split_name="disambig",
    )
    outcomes = {**ambig_outcomes, **disambig_outcomes}

    train_ids, dev_ids, test_ids = split_ids(frame, args.random_seed)
    train_df = frame[frame["group_id"].isin(train_ids)].copy()
    dev_df = frame[frame["group_id"].isin(dev_ids)].copy()
    test_df = frame[frame["group_id"].isin(test_ids)].copy()

    models = build_models(args.random_seed)

    summary = {
        "random_seed": args.random_seed,
        "condition": args.condition,
        "harm_budget": args.harm_budget,
        "target_trigger_min": args.target_trigger_min,
        "target_trigger_max": args.target_trigger_max,
        "splits": {
            "train_rows": len(train_df),
            "dev_rows": len(dev_df),
            "test_rows": len(test_df),
            "train_risk_positive": int(train_df["risk_positive"].sum()),
            "dev_risk_positive": int(dev_df["risk_positive"].sum()),
            "test_risk_positive": int(test_df["risk_positive"].sum()),
        },
        "models": {},
    }

    csv_rows = []

    for model_name, model in models.items():
        model.fit(train_df, train_df["risk_positive"])
        dev_scores = model.predict_proba(dev_df)[:, 1]
        test_scores = model.predict_proba(test_df)[:, 1]
        dev_score_map = dict(zip(dev_df["group_id"], dev_scores))
        test_score_map = dict(zip(test_df["group_id"], test_scores))

        dev_sweep = threshold_sweep(dev_df, outcomes, dev_score_map)
        chosen = choose_threshold(
            dev_sweep,
            target_trigger_min=args.target_trigger_min,
            target_trigger_max=args.target_trigger_max,
            harm_budget=args.harm_budget,
        )
        test_metrics = evaluate_policy(test_df, outcomes, test_score_map, chosen["threshold"])
        auc_all = roc_auc_score(test_df["risk_positive"], test_scores)
        transitioned_mask = test_df["has_transition"] == 1
        if transitioned_mask.sum() > 1 and test_df.loc[transitioned_mask, "risk_positive"].nunique() > 1:
            auc_transitioned = roc_auc_score(
                test_df.loc[transitioned_mask, "risk_positive"],
                np.array(test_scores)[transitioned_mask.to_numpy()],
            )
        else:
            auc_transitioned = float("nan")

        summary["models"][model_name] = {
            "test_auc_risk_positive_all": auc_all,
            "test_auc_risk_positive_transitioned": auc_transitioned,
            "chosen_threshold_from_dev": chosen,
            "test_metrics": test_metrics,
        }
        csv_rows.append(
            {
                "model": model_name,
                "test_auc_risk_positive_all": auc_all,
                "test_auc_risk_positive_transitioned": auc_transitioned,
                **test_metrics,
            }
        )

    baseline_rows = []
    for baseline_name, condition_key in [
        ("vanilla", "vanilla"),
        ("blanket_redirect", "intervention"),
        ("always_reflect", "always_reflect"),
    ]:
        metrics = baseline_metrics(test_df, outcomes, condition_key)
        summary["models"][baseline_name] = {"test_metrics": metrics}
        baseline_rows.append({"model": baseline_name, **metrics})

    write_csv(Path(args.output_csv), csv_rows + baseline_rows)
    write_json(Path(args.output_json), summary)

    lines = [
        "# Selective Trigger Model Evaluation",
        "",
        f"- Condition: `{args.condition}`",
        "- Protocol: strict-online (no future-info features; no-transition samples never trigger)",
        f"- Harm budget on dev: `{args.harm_budget:.2%}`",
        f"- Target trigger band on dev: `{args.target_trigger_min:.0%}` - `{args.target_trigger_max:.0%}`",
        "",
        "## Split Sizes",
        "",
        f"- Train rows: `{summary['splits']['train_rows']}` (risk-positive `{summary['splits']['train_risk_positive']}`)",
        f"- Dev rows: `{summary['splits']['dev_rows']}` (risk-positive `{summary['splits']['dev_risk_positive']}`)",
        f"- Test rows: `{summary['splits']['test_rows']}` (risk-positive `{summary['splits']['test_risk_positive']}`)",
        f"- Test rows with transition: `{int(test_df['has_transition'].sum())}`",
        "",
        "## Selective Policies (held-out test)",
        "",
        "| model | test_auc_all | test_auc_transitioned | threshold | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit | avg_generated_tokens | avg_token_delta_vs_vanilla |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in csv_rows:
        lines.append(
            f"| {row['model']} | {row['test_auc_risk_positive_all']:.4f} | {row['test_auc_risk_positive_transitioned']:.4f} | {row['threshold']:.6f} | {row['trigger_rate']:.4f} | {row['ambig_correction_rate']:.4f} | {row['disambig_harm_rate']:.4f} | {row['net_benefit']} | {row['avg_generated_tokens']:.2f} | {row['avg_token_delta_vs_vanilla']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Baselines On Same Test Subset",
            "",
            "| model | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit | avg_generated_tokens | avg_token_delta_vs_vanilla |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in baseline_rows:
        lines.append(
            f"| {row['model']} | {row['trigger_rate']:.4f} | {row['ambig_correction_rate']:.4f} | {row['disambig_harm_rate']:.4f} | {row['net_benefit']} | {row['avg_generated_tokens']:.2f} | {row['avg_token_delta_vs_vanilla']:.2f} |"
        )

    output_md = Path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote csv to {args.output_csv}")
    print(f"Wrote json to {args.output_json}")
    print(f"Wrote md to {args.output_md}")
    print(json.dumps(summary["models"], ensure_ascii=False))


if __name__ == "__main__":
    main()
