# Current Pilot Scope

## Related notes
- [Docs Index](../index.md)
- [BARR Mainline Claim](../research/framing/barr-mainline.md)
- [EMNLP 2026 Storyline](../research/framing/emnlp-2026-storyline.md)
- [Week 1 Transition Probe Plan](../experiments/plans/week1-transition-probe.md)
- [2026-04-07 Weekly Summary](weekly/2026-04-07-weekly.md)

## Core Question

The current go/no-go question is not broad benchmarking.

It is:

> Can Qwen3-8B transition-point internal states predict future biased answers on BBQ ambiguous samples well enough to justify BARR as a selective intervention method?

## Current Phase

The project is currently in the transition from **Phase B** to **Phase C**.

- **Phase A complete**: transition recurrence was established as a strong trajectory-level risk marker.
- **Phase B complete**: full-shard BF16 run on `age + religion` passed the hidden-state gate at `k=2` and `k=3`.
- **Phase C running**: timing ablation is testing `no_intervention / t-1 / t / t+1 / random` around `k=2` and `k=3`.

## Active Scope

- **Model**: `Qwen/Qwen3-8B` BF16 for the current mechanistic pilot.
- **Dataset**: BBQ ambiguous split.
- **Primary categories**: `age`, `religion`.
- **Primary signal**: Layer-28 transition-state separation.
- **Primary decision target**: whether transition-aware timing beats non-timed controls strongly enough to support BARR's intervention story.

## Current Decision Rules

### What already counts as a Phase B pass

- Hidden-state gate:
  transition-window biased-vs-correct separation exceeds matched non-transition controls.

- Margin gate:
  Unknown-logit margin may support the claim, but it is not required if hidden-state separation is already clearly positive.

### What Phase C needs to answer

1. Is `k=2` a stronger intervention window than `k=3`?
2. Is transition-aware timing (`t-1 / t / t+1`) meaningfully better than `random` timing?
3. Is the effect robust enough to support the paper framing that transition points are actionable intervention windows?

## Current Evidence Snapshot

Phase B full-shard result:

| transition_order | transition_dist | control_dist | hidden_gate | margin_gate |
|---:|---:|---:|:---:|:---:|
| 2 | 86.58 | 56.40 | ✅ | ❌ |
| 3 | 58.94 | 39.45 | ✅ | ❌ |

Interpretation:

- The strongest current justification for continuing is **hidden-state separation**, not Unknown-logit margin.
- `k=2` is the strongest first candidate for Phase C.

## Working Rules

- Keep the pipeline narrow and evidence-first.
- Prefer the current narrowed transition-probe path over reviving broad old scaffolding.
- Do not promote Unknown-logit margin to a main mechanism claim unless new evidence changes that.
- Update this note when the project focus changes, not for every small experiment.
