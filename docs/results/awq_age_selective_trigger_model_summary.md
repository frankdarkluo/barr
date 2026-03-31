# Selective Trigger Model Evaluation

- Condition: `redirect`
- Harm budget on dev: `5.00%`
- Target trigger band on dev: `10%` - `20%`

## Split Sizes

- Train rows: `2208` (risk-positive `200`)
- Dev rows: `736` (risk-positive `67`)
- Test rows: `736` (risk-positive `67`)

## Selective Policies (held-out test)

| model | test_auc_risk_positive | threshold | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit |
|---|---:|---:|---:|---:|---:|---:|
| position_only_lr | 0.6609 | 0.650204 | 0.1277 | 0.2200 | 0.0526 | -8 |
| text_level_lr | 0.9604 | 0.666948 | 0.1128 | 0.8000 | 0.0222 | 32 |

## Baselines On Same Test Subset

| model | trigger_rate | ambig_correction_rate | disambig_harm_rate | net_benefit |
|---|---:|---:|---:|---:|
| vanilla | 0.0000 | 0.0000 | 0.0000 | 0 |
| blanket_redirect | 1.0000 | 1.0000 | 0.4321 | -106 |
| always_reflect | 1.0000 | 0.8800 | 0.0776 | 16 |