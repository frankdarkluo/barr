# Selective Trigger Model Evaluation

- Condition: `redirect`
- Protocol: strict-online (no future-info features; no-transition samples never trigger)
- Harm budget on dev: `5.00%`
- Target trigger band on dev: `10%` - `20%`

## Split Sizes

- Train rows: `2208` (risk-positive `200`)
- Dev rows: `736` (risk-positive `67`)
- Test rows: `736` (risk-positive `67`)
- Test rows with transition: `713`

## Selective Policies (held-out test)

| model | test_auc_all | test_auc_transitioned | threshold | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit | avg_generated_tokens | avg_token_delta_vs_vanilla |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| position_only_lr | 0.6609 | 0.6488 | 0.650204 | 0.1277 | 0.2200 | 0.0526 | -8 | 12.85 | 12.85 |
| text_level_lr | 0.9049 | 0.9015 | 0.716556 | 0.0870 | 0.7000 | 0.0139 | 30 | 8.56 | 8.56 |

## Baselines On Same Test Subset

| model | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit | avg_generated_tokens | avg_token_delta_vs_vanilla |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 0.0000 | 0.0000 | 0.0000 | 0 | 0.00 | 0.00 |
| blanket_redirect | 1.0000 | 1.0000 | 0.4321 | -106 | 98.34 | 98.34 |
| always_reflect | 1.0000 | 0.8800 | 0.0776 | 16 | 11.00 | 11.00 |