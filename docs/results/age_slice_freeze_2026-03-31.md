# AWQ Age Slice Freeze (2026-03-31)

## Scope

This freeze locks the English BBQ age-slice selective-trigger result used as the Week 2 reference point.

## Protocol Lock

- Data split: held-out train/dev/test
- Threshold selection: dev only
- Reporting: test only
- Trigger protocol: strict-online
- No-transition samples: never trigger
- Default trigger model: `text_level_lr`

Reference artifacts:
- `outputs/transition_probe/interventions/awq_age_selective_trigger_model_strict_online_summary.md`
- `outputs/transition_probe/interventions/awq_age_selective_trigger_model_strict_online_table.csv`

## Frozen Core Numbers (held-out test)

Selective policy (`text_level_lr`):
- trigger_rate: `0.0870`
- ambig_correction_rate: `0.7000`
- disambig_harm_rate: `0.0139`
- net_benefit: `+30`

Baselines on the same test subset:
- vanilla: correction `0.0000`, harm `0.0000`, net `0`
- blanket_redirect: correction `1.0000`, harm `0.4321`, net `-106`
- always_reflect: correction `0.8800`, harm `0.0776`, net `+16`

## Interpretation Lock

- Blanket redirect remains high-impact but high-harm.
- Always-reflect is safer than blanket redirect but still over-triggers.
- Selective BARR (`text_level_lr`) remains the best utility-harm balance under strict-online constraints.

## Week 2 Usage Rule

For expansion phases, keep this as the default trigger baseline unless a later full-category run clearly and reproducibly improves both:
1. net benefit, and
2. disambig harm constraint.
