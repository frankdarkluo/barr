# AWQ Age Selective Trigger Overview

## Related notes
- [AWQ Age Intervention Main Table](awq-age-intervention-main-table.md)
- [BARR Mainline Claim](../../../research/framing/barr-mainline.md)
- [Stage 1 / Stage 2 Claude Handoff](../../../research/reviews/stage1-stage2-claude-handoff.md)
- Archived source notes:
  - [Age Slice Freeze](../../../archive/experiments/results/age/age-slice-freeze-2026-03-31.md)
  - [Threshold-Only Trigger Summary](../../../archive/experiments/results/age/awq-age-selective-trigger-summary.md)
  - [Model Trigger Summary](../../../archive/experiments/results/age/awq-age-selective-trigger-model-summary.md)
  - [Strict-Online Model Trigger Summary](../../../archive/experiments/results/age/awq-age-selective-trigger-model-strict-online-summary.md)

## Why This Note Exists

This note consolidates the overlapping AWQ age selective-trigger summaries into one main entry point.
The archived source notes are preserved for provenance, but this is now the canonical overview for the age slice.

## One-Line Takeaway

The age slice is the clearest current evidence that selective transition-time triggering is the useful contribution:
blanket redirect corrects almost everything but causes unacceptable harm, while strict-online selective BARR keeps much of the correction benefit with much lower harm.

## Threshold-Only Trigger Snapshot

Risk score: first transition token index  
Intervention condition: `redirect`

| threshold | trigger_count | trigger_rate | ambig_corrected | ambig_correction_rate | disambig_harmed | disambig_harm_rate | net_benefit |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 218 | 348 | 0.0946 | 90 | 0.3629 | 75 | 0.0423 | 15 |
| 212 | 399 | 0.1084 | 97 | 0.3911 | 84 | 0.0474 | 13 |

Interpretation:
- Transition timing alone is useful.
- But it is not yet precise enough to be the preferred deployed trigger.

## Model-Based Trigger Snapshot

Held-out test set, same `redirect` condition:

| model | test_auc_risk_positive | threshold | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit |
|---|---:|---:|---:|---:|---:|---:|
| position_only_lr | 0.6609 | 0.650204 | 0.1277 | 0.2200 | 0.0526 | -8 |
| text_level_lr | 0.9604 | 0.666948 | 0.1128 | 0.8000 | 0.0222 | 32 |

Interpretation:
- Adding a text-level model improves utility sharply over a position-only trigger.
- The `text_level_lr` policy becomes the first clearly positive-utility selective trigger on this slice.

## Strict-Online Frozen Protocol

Protocol:
- no future-info features
- no-transition samples never trigger
- held-out train/dev/test
- harm budget on dev: `5%`

| model | test_auc_all | test_auc_transitioned | threshold | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit | avg_generated_tokens | avg_token_delta_vs_vanilla |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| position_only_lr | 0.6609 | 0.6488 | 0.650204 | 0.1277 | 0.2200 | 0.0526 | -8 | 12.85 | 12.85 |
| text_level_lr | 0.9049 | 0.9015 | 0.716556 | 0.0870 | 0.7000 | 0.0139 | 30 | 8.56 | 8.56 |

Baselines on the same test subset:

| model | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit | avg_generated_tokens | avg_token_delta_vs_vanilla |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 0.0000 | 0.0000 | 0.0000 | 0 | 0.00 | 0.00 |
| blanket_redirect | 1.0000 | 1.0000 | 0.4321 | -106 | 98.34 | 98.34 |
| always_reflect | 1.0000 | 0.8800 | 0.0776 | 16 | 11.00 | 11.00 |

## Freeze Decision

The age slice freeze locked this interpretation:

- `text_level_lr` under strict-online protocol is the default age-slice reference policy.
- Blanket redirect remains a useful upper-bound correction baseline, not a viable deployment policy.
- Always-reflect is safer than blanket redirect, but still clearly over-triggers relative to selective BARR.

Frozen core numbers:

- trigger_rate: `0.0870`
- ambig_correction_rate: `0.7000`
- disambig_harm_rate: `0.0139`
- net_benefit: `+30`

## Recommended Reading Order

1. Read this note for the age-slice story.
2. Use [AWQ Age Intervention Main Table](awq-age-intervention-main-table.md) for raw intervention comparisons.
3. Use [BARR Mainline Claim](../../../research/framing/barr-mainline.md) for how these results support the paper framing.
