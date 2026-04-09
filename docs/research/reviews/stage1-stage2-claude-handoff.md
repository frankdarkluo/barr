# Stage 1 / Stage 2 Claude Handoff

## Related notes
- [Docs Index](../../index.md)
- [BARR Mainline Claim](../framing/barr-mainline.md)
- [AWQ Age Selective Trigger Overview](../../experiments/results/age/awq-age-selective-trigger-overview.md)

Date: 2026-03-31
Owner: Codex execution lane
Purpose: Confirm method framing and next-step scope after Stage 1 and Stage 2 execution.

## Executive Summary

- Stage 1 complete: planning, risk identification, and minimal executable slices were finished.
- Stage 2 complete: critical experiments and diagnostics were executed to resolve the core bottleneck.
- Main finding: failure was not ranking quality; failure was trigger-time false positives on disambig samples.

## Causal Finding (Final)

1. Detection ranking is strong across slices (AUC mostly around 0.90+).
2. Utility collapse came from disambig false positives leaking into intervention triggers.
3. Adding an online-available context-aware gate (higher trigger bar for disambig-like contexts) removes most harmful triggers.
4. Under a unified protocol, net utility flips positive across viable slices.

## Unified Results (Baseline vs Context-Shifted)

| category | baseline net | context_shifted net | delta net | baseline harm_rate | shifted harm_rate |
|---|---:|---:|---:|---:|---:|
| age | +30 | +35 | +5 | 0.0139 | 0.0000 |
| disability_status | 0 | +6 | +6 | 0.0382 | 0.0000 |
| religion | 0 | +5 | +5 | 0.0686 | 0.0196 |
| ses | -7 | +9 | +16 | 0.0243 | 0.0000 |

Interpretation:
- Ambig correction is preserved.
- Harm drops sharply.
- Net benefit improves in every listed category.

## Method Definition To Lock

Two-stage BARR trigger policy:

1. Stage 1 (risk scoring): text-level model scores risk at transition point.
2. Stage 2 (context-aware gating): trigger threshold is adjusted upward for disambig-like contexts.

This is the main method contribution supported by the current evidence.

## Scope Boundaries and Non-Claims

- gender_identity: no biased positives in test; report as no correction opportunity, not method failure.
- physical_appearance: currently low precision and negative utility under prior setup; keep as limitation unless improved by additional targeted gating.
- nationality, race_ethnicity, sexual_orientation: current AWQ ambig slice has 0 biased positives (n=22 each); not suitable for trigger utility claims in current form.

## Decisions Needed From Claude

1. Paper framing: treat two-stage trigger as the central method, with trigger precision as first-class metric.
2. Reporting scope: main table on age + disability_status + religion + ses; limitation rows for the others.
3. Next experiments: prioritize BF16 comparison on age + disability_status + ses to validate deployment story robustness.

## Minimal Artifact Set

- outputs/transition_probe/interventions/phase4b_context_filter_unified_table.csv
- outputs/transition_probe/interventions/phase4b_context_filter_unified_table.md
- outputs/transition_probe/interventions/phase4b_age_context_filter_summary.json
- outputs/transition_probe/interventions/phase4b_disability_context_filter_summary.json
- outputs/transition_probe/interventions/phase4b_religion_context_filter_summary.json
- outputs/transition_probe/interventions/phase4b_ses_context_filter_summary.json
- outputs/transition_probe/interventions/awq_phase4_trigger_precision_summary.csv
