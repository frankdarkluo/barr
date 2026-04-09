# EMNLP 2026 Storyline

## Related notes
- [Docs Index](../../index.md)
- [Current Pilot Scope](../../progress/current-pilot-scope.md)
- [BARR Mainline Claim](barr-mainline.md)
- [Week 1 Transition Probe Plan](../../experiments/plans/week1-transition-probe.md)

## One-Sentence Thesis

Quantization increases fairness risk in reasoning models, and transition-aware redirection offers a practical, efficient intervention because biased trajectories become detectable and steerable at transition points.

## Core Paper Claim

The paper should not be framed as:
- "we found a cool hidden-state probe"

It should be framed as:
- "transition points are actionable fairness intervention windows"
- "a transition-aware redirect improves fairness more efficiently than post-hoc reflection"
- "this matters especially under quantized deployment"

## Narrative Arc

### Part 1: Why This Matters

- Reasoning models are increasingly deployed in quantized form.
- Quantization changes reasoning behavior, not just accuracy.
- For fairness-sensitive QA, the problem is not only final answer bias but biased reasoning trajectories.

### Part 2: Key Mechanistic Observation

- On BBQ ambiguous questions, biased trajectories diverge at transition points.
- This signal is not just generic late-stage reasoning state.
- Transition-point hidden states predict future biased answers better than matched nearby non-transition states.

Current evidence:
- `position_only` is strong, so transition timing matters.
- `position + hidden` improves over `position_only`, so hidden state adds residual information.
- `transition_hidden` clearly outperforms `matched_control_hidden`, so the signal is transition-specific.

### Part 3: Why Detection Matters

- Detection is not the end goal.
- Detection matters because it enables selective intervention at the right moment.
- The paper's central contribution is not just identifying risky trajectories, but using that signal to intervene early.

### Part 4: Main Method Claim

- Simply stopping early is not enough.
- Stopping and redirecting reasoning is what works.

Current pilot evidence on BF16 Qwen3-8B, BBQ ambiguous, biased subset:
- `vanilla`: `0/29` corrected
- `exit`: `9/29` corrected
- `redirect`: `28/29` corrected
- `always_reflect`: `26/29` corrected

This is the main empirical contrast:
- early exit alone is weak
- redirect is strong
- redirect can outperform a reflection-style baseline
- the next critical control is `random redirect`, to test whether transition-aware timing matters beyond the prompt itself

### Part 5: Deployment Story

- The BF16 pilot establishes the mechanism.
- The deployment story requires quantization.
- The real paper value appears when the same transition-aware redirect still works on AWQ-Int4, where biased trajectories should be more common.

## What Must Be True For The Paper To Land

These are the non-negotiables:

1. Quantized models show a stronger fairness problem than BF16.
2. Transition-aware redirect still corrects a large fraction of biased trajectories under quantization.
3. The trigger cost is lower than always-reflect when measured end-to-end on all samples.
4. Detection numbers are reported with sample-grouped evaluation, not trajectory-random CV.
5. BARR must not substantially harm samples that were already correct before intervention.

## What We Should Not Oversell

- Do not oversell the current BF16 detection AUROC as final, because current multi-seed trajectories reuse the same sample IDs.
- Do not oversell LOCO as a decisive test on BF16, because positive counts are still small.
- Do not oversell current always-reflect token efficiency, because that baseline implementation is still too light.

## Reviewer-Safe Claim Template

Use wording closer to:

> We find that fairness failures in reasoning models concentrate around transition points, where biased trajectories become detectable and unusually responsive to intervention. Leveraging this structure, BARR selectively redirects risky reasoning paths and improves fairness more efficiently than post-hoc reflection, especially in quantized deployment settings.

And pair it with a limitation sentence like:

> Our current evaluation focuses on ambiguous QA settings where bias is most readily triggered; extending the framework to open-ended generation remains future work.

Avoid wording like:

> We discovered the hidden bias circuit.

## Priority Order

### Priority 1

- Sample-grouped detection evaluation
- AWQ-Int4 replication of detection and redirect

### Priority 2

- Stronger always-reflect baseline
- End-to-end trigger evaluation on all samples

### Priority 3

- CBBQ Chinese validation

### Priority 4

- LOCO on the larger AWQ biased set
- StereoSet only if time remains

## Target Tables

### Table 1

Correction rate on biased trajectories:
- Vanilla
- Early Exit
- Random Redirect
- Always-Reflect
- BARR

Across:
- EN BF16
- EN AWQ-Int4
- CN BF16
- CN AWQ-Int4

### Table 2

End-to-end efficiency on all samples:
- Trigger rate
- Net fairness improvement
- Accuracy / fairness retention on originally correct samples
- Average extra tokens per query
- Average extra tokens on triggered queries

### Table 3

Detection validation:
- sample-grouped AUROC
- transition vs matched control
- possibly position-only vs position+hidden

## Immediate Next Experiments

1. Recompute detection with sample-grouped splits by `sample_id`.
2. Run the full AWQ-Int4 English BBQ pipeline.
3. Fix always-reflect into a genuinely strong baseline.
4. Evaluate trigger rate, net cost, and collateral damage on all samples, not only biased subsets.
5. Add `random redirect` as the key timing-control baseline.

## Current Bottom Line

The project already has a credible EMNLP paper seed.

The BF16 pilot is no longer asking whether BARR exists.
It is now asking whether the full deployment story survives:
- quantization
- fair baselines
- end-to-end trigger accounting
