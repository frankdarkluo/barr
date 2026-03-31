Week 1 Pilot Study: Quantization x Reasoning x Fairness on Qwen3-8B

Goal
----
Verify three things:
1. Does quantization change fairness on reasoning-based QA?
2. Is 4-bit more harmful than 8-bit on this setting?
3. Can we evaluate the change automatically without any LLM-as-a-judge?

Scope
-----
Model family:
- Qwen3-8B BF16
- Qwen3-8B GPTQ-Int8
- Qwen3-8B AWQ-Int4
- optional: Qwen3-8B GPTQ-Int4

Datasets:
- MBBQ ambiguous split
- OpenMBBQ ambiguous split
Languages:
- English
- Chinese
- Urdu
Use 200 samples per language per dataset for pilot.

Important design choice
-----------------------
Do NOT use LLM-as-a-judge.
For OpenMBBQ, modify the prompt so the model still reasons freely, but the final answer must be:
<answer>A</answer> or <answer>B</answer> or <answer>C</answer>
where C = Unknown / Cannot be determined.

This keeps the task open-ended at the reasoning level, but makes evaluation fully rule-based.

Primary automatic metrics
-------------------------
1. Accuracy
2. Bias score / stereotypical choice rate on ambiguous items
3. Unknown rate
4. Pairwise counterfactual consistency:
   for paired items differing only in protected-group wording,
   measure whether the final answer changes
5. Group gap:
   absolute difference of model outcome statistics across groups

Reasoning sidecar metrics (NOT fairness metrics)
------------------------------------------------
1. think token length
2. total generated tokens
3. latency
4. token entropy / TECA-style curve if logits are available
5. early-answer position probe (optional)

Outputs to save for every sample
--------------------------------
- sample_id
- language
- dataset
- quantization
- protected attribute category
- prompt
- raw output
- reasoning text
- final parsed answer
- accuracy label
- stereotype label
- unknown label
- token count
- latency

Scripts
-------
1. run_inference.py
   run all models and save jsonl outputs

2. parse_answers.py
   extract A/B/C from <answer> tags
   validate parsing success

3. eval_fairness.py
   compute accuracy, bias score, unknown rate, group gap

4. eval_counterfactual.py
   compute pairwise answer-flip rate and consistency

5. analyze_reasoning_dynamics.py
   compute token length, latency, entropy-based stats

6. summarize_week1.py
   generate:
   - main_table.csv
   - per_language_table.csv
   - case_studies.jsonl
   - week1_summary.md

Success criteria
----------------
Week 1 is successful if at least one of the following holds:
A. 4-bit quantization worsens fairness relative to BF16 on at least one dataset/language
B. fairness degradation is larger in Urdu than in English/Chinese
C. fairness degradation co-occurs with measurable reasoning-dynamics shifts
   (e.g. shorter/longer thinking, entropy changes, instability)

Decision rule after Week 1
--------------------------
If A or B holds:
- continue to Week 2 method design
- prioritize a Fair-GPTQ-like or benchmark/metric paper direction

If only C holds:
- continue, but frame the project as reasoning-aware fairness evaluation first

If none hold:
- do not start a quantization-aware debiasing method yet
- pivot toward benchmark or metric design