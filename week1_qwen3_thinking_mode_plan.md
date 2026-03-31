# Week 1 Pilot Study Plan for Qwen3-8B Thinking Mode

## Core conclusion

Your current setup is already close to supporting **Qwen3-8B thinking mode**.

The main takeaway is:

- **The metric layer can stay mostly unchanged**
- The main changes are in **inference**, **prompting**, and **parsing**
- `diff_bias_score.py` can remain the automatic evaluation metric reference
- `vanilla.py` should be lightly adapted to support **Qwen3-8B thinking mode**

A key structural issue to fix first:

- `diff_bias_score.py` reads ground truth from `data/{dataset}/updates/{category}.jsonl`
- `vanilla.py` reads from `data/{dataset}/{category}.jsonl`

These should be unified before running the pilot, otherwise results may not align cleanly.

---

## What to keep

### `diff_bias_score.py`
This is a reasonable starting point for the **automatic evaluation metric** in Week 1.

It already computes a **differential bias score** by comparing model predictions with stereotypical targets, and uses fields such as:

- `answer`
- `answer_text`
- `correct`
- `correct_answer_id`

So the main requirement is to make sure `vanilla.py` outputs these fields consistently.

### `vanilla.py`
This is already a strong base runner because it:

- supports multilingual prompting
- enforces `<answer> ... </answer>` style output
- stores raw model response
- maps free-form answers back to `ans0 / ans1 / ans2`

That means you do **not** need to redesign the whole pipeline.

---

## What needs to change for Qwen3-8B thinking mode

### 1. Explicitly enable thinking mode

For this pilot, do not assume Qwen3 will always think in the exact way you want by default.

Recommended approach:

- explicitly append `/think` to the prompt when using Qwen3
- if tokenizer version supports it, pass `enable_thinking=True` to `apply_chat_template`

This makes the behavior easier to control and easier to reproduce.

### 2. Separate reasoning text from final answer

You should save both:

- the **full raw response**
- the extracted **reasoning trace**
- the extracted **final answer text**
- the mapped answer id (`ans0`, `ans1`, `ans2`)

This is important because Week 1 is not only about bias score, but also about checking whether Qwen3 thinking mode behaves stably enough for later quantization experiments.

### 3. Do not start with `temperature=0.0`

For compatibility testing, greedy decoding is a bad first choice for Qwen3 thinking mode.

Use a first sanity-check run with a non-greedy setup. After the pipeline works, you can decide whether to move to a more deterministic setting for fairness comparison.

### 4. Do not compute metrics inline during generation

Right now `write_jsonl()` in `vanilla.py` also computes metrics.

For the pilot, it is cleaner to split the pipeline into:

1. **generate outputs**
2. **run `diff_bias_score.py` separately**

This makes debugging much easier and avoids confusion from path mismatches and mixed output formats.

---

## Recommended Week 1 pilot scope

Start narrow.

### Task
- `bbq`
- `profession`
- `ambig`
- `en`

### Model
- `Qwen/Qwen3-8B` BF16 first

### Goal
Verify that:

1. the model runs in thinking mode correctly
2. the `<answer>` extraction works
3. the mapped `answer` field is correct
4. `diff_bias_score.py` can score the outputs without extra manual fixes

Only after this is stable should you move to quantized variants.

---

## Minimal changes to `vanilla.py`

### Add two arguments

```python
parser.add_argument("--force_think", action="store_true")
parser.add_argument("--extract_reasoning", action="store_true")
```

### Modify prompt formatting

```python
def format_prompt(example, args):
    config = LANGUAGE_CONFIG.get(args.language, LANGUAGE_CONFIG['en'])
    prompt = config["user_template"].format(
        context=example['context'],
        question=example['question'],
        ans0=example['ans0'],
        ans1=example['ans1'],
        ans2=example['ans2']
    )
    if args.force_think and "Qwen3" in args.model_name_or_path:
        prompt = prompt + "\n/think"
    return prompt
```

### Modify `apply_chat_template`

```python
try:
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True if "Qwen3" in args.model_name_or_path else None
    )
except TypeError:
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
```

### Extract reasoning and answer separately

```python
generated_text = output.outputs[0].text

reasoning_text = ""
m_reason = re.search(r"<think>(.*?)</think>", generated_text, flags=re.S)
if m_reason:
    reasoning_text = m_reason.group(1).strip()

m_answer = re.search(r"<answer>\s*(.*?)\s*</answer>", generated_text, flags=re.S | re.I)
if m_answer:
    final_answer = m_answer.group(1).strip()
else:
    final_answer = generated_text.strip()

final_answer_id = map_answer_text_to_id(
    final_answer,
    state["question_data"],
    language=args.language
)

gold_answer = "ans" + str(state["question_data"]["label"])
correct = int(final_answer_id == gold_answer)

state["output_dict"] = {
    "correct": correct,
    "answer": final_answer_id,
    "answer_text": final_answer,
    "correct_answer_id": gold_answer,
    "response": generated_text,
    "reasoning_text": reasoning_text,
    "system_prompt": sys_prompt,
    "problem": state["problem"],
    "quantization": args.quantization if args.quantization else "full_precision",
    "question": state["question_data"],
}
```

---

## Suggested execution order

### Step 1
Run one small BF16 test with Qwen3-8B in English only.

### Step 2
Check a few outputs manually:
- does the model actually produce a usable answer?
- does `<answer>...</answer>` parse correctly?
- is reasoning text stored cleanly?

### Step 3
Run `diff_bias_score.py` on the saved output.

### Step 4
Only after the chain works, add quantized Qwen3 variants.

---

## Week 1 success condition

Week 1 is successful if you can establish a stable pipeline with:

- Qwen3-8B thinking mode
- structured answer extraction
- automatic evaluation through `diff_bias_score.py`
- reusable saved outputs for later quantization experiments

That is enough for Week 1.

You do **not** need to solve the full fairness-method problem in the first week.

---

## Final practical recommendation

So the decision is:

**Yes, your current codebase can be adapted to Qwen3-8B thinking mode.**

And the adaptation is **small**, not a rewrite.

The immediate work is:

1. unify GT paths
2. explicitly control Qwen3 thinking mode
3. store reasoning and final answer separately
4. separate generation from evaluation
5. test on a narrow English BBQ pilot first

Once that is stable, you can move on to quantization.
