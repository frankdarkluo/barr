# Phase 2 Viable Categories And Phase 3 Deployment Stress Test

## Related notes
- [Docs Index](../../index.md)
- [Current Pilot Scope](../../progress/current-pilot-scope.md)
- [BARR Mainline Claim](../../research/framing/barr-mainline.md)
- [EMNLP 2026 Storyline](../../research/framing/emnlp-2026-storyline.md)
- [Stage 1 / Stage 2 Claude Handoff](../../research/reviews/stage1-stage2-claude-handoff.md)
- [AWQ Shared Strict-Online Progress](../results/shared/awq-shared-strict-online-progress.md)

## Purpose

Freeze the next paper-facing phases after the BF16 protocol cleanup:

1. expand the main result from a single age slice to the four viable categories
2. treat quantization as a deployment stress test, not yet as the sole novelty anchor

## Phase 2

Window:
- April 18, 2026 to April 27, 2026

Goal:
- move the paper-facing main table from `age` only to the four viable categories:
  - `age`
  - `disability_status`
  - `religion`
  - `ses`

Why these four:
- Stage 1 / Stage 2 already shows positive or improved net benefit after the context-aware gate:
  - `age`: `+30 -> +35`
  - `disability_status`: `0 -> +6`
  - `religion`: `0 -> +5`
  - `ses`: `-7 -> +9`
- harm drops materially in all four.
- this is the strongest current reviewer-safe scope for the selective-intervention story.

Main-table rule:
- the main policy table should include only these four categories.
- all other categories should move to limitation or appendix unless they later show stable biased positives and stable utility.

Limitation categories for now:
- `gender_identity`: no biased positives in test
- `nationality`: no biased positives in current AWQ ambiguous slice
- `race_ethnicity`: no biased positives in current AWQ ambiguous slice
- `sexual_orientation`: no biased positives in current AWQ ambiguous slice
- `physical_appearance`: utility too unstable under prior setup

Phase 2 deliverables:
- one main table over the four viable categories
- one limitation table or note for the remaining categories
- one short paper-facing summary explaining why the reporting scope is intentionally narrowed

Phase 2 decision rule:
- if the four-category table stays positive on net benefit with transparent harm accounting, keep it as the paper's main scope.
- do not broaden to all categories just for coverage.

## Phase 3

Window:
- April 28, 2026 to May 6, 2026

Goal:
- evaluate quantization as a deployment stress test for the same selective-intervention policy

Framing to lock:
- main novelty: selective intervention policy
- quantization: deployment-motivated stress test that may strengthen the motivation and practical value

Why this is safer:
- the current shared strict-online pooled policy is not yet stable:
  - `trigger_rate ≈ 0.000889`
  - `ambig_correction_rate = 0`
  - `disambig_harm_rate = 0`
  - `net_benefit = 0`
- this means the current repo does not yet support a strong pooled-global quantization-first story.

Reviewer-safe comparison:
- keep the protocol fixed
- compare `BF16` vs `AWQ-Int4`
- compare them on the same four viable categories

Phase 3 decision rule:
- if the quantization effect is stable across the four viable categories, it can move up toward title-level framing.
- if it is mixed or unstable, keep it as a secondary deployment table and do not bind the whole paper to it.

## Non-Goals

- do not revive a broad all-category benchmarking story for the main paper table
- do not make quantization the sole novelty before the four-category selective-intervention story is stable
- do not claim a pooled global trigger policy is already deployment-ready
