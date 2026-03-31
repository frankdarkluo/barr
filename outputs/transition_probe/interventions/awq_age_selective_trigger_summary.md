# Selective Trigger Evaluation

Risk score: first transition token index
Intervention condition: `redirect`

- Ambig biased base: `248`
- Disambig correct base: `1773`

## Best Net Benefit

| threshold | trigger_count | trigger_rate | ambig_corrected | ambig_correction_rate | disambig_harmed | disambig_harm_rate | net_benefit |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 218 | 348 | 0.0946 | 90 | 0.3629 | 75 | 0.0423 | 15 |

## Best In Target Trigger Band

Target band: `0.10` - `0.20`

| threshold | trigger_count | trigger_rate | ambig_corrected | ambig_correction_rate | disambig_harmed | disambig_harm_rate | net_benefit |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 212 | 399 | 0.1084 | 97 | 0.3911 | 84 | 0.0474 | 13 |
