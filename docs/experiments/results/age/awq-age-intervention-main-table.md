# AWQ Age Intervention Main Table

## Related notes
- [AWQ Age Selective Trigger Overview](awq-age-selective-trigger-overview.md)
- [BARR Mainline Claim](../../../research/framing/barr-mainline.md)
- [Stage 1 / Stage 2 Claude Handoff](../../../research/reviews/stage1-stage2-claude-handoff.md)

## ambig

| condition | n_base | corrected_to_correct | corrected_rate | escaped_biased | escaped_rate | avg_generated_tokens_on_base |
|---|---:|---:|---:|---:|---:|---:|
| always_reflect | 248 | 195 | 0.7863 | 195 | 0.7863 | 11.00 |
| exit | 248 | 33 | 0.1331 | 39 | 0.1573 | 20.03 |
| random_redirect | 248 | 248 | 1.0000 | 248 | 1.0000 | 99.77 |
| redirect | 248 | 247 | 0.9960 | 247 | 0.9960 | 93.64 |

## disambig

| condition | n_base | harmed | harm_rate | harmed_to_biased | harmed_to_biased_rate | avg_generated_tokens_on_base |
|---|---:|---:|---:|---:|---:|---:|
| always_reflect | 1773 | 140 | 0.0790 | 1 | 0.0006 | 11.06 |
| exit | 1773 | 70 | 0.0395 | 15 | 0.0085 | 29.08 |
| random_redirect | 1773 | 859 | 0.4845 | 0 | 0.0000 | 114.11 |
| redirect | 1773 | 788 | 0.4444 | 0 | 0.0000 | 111.41 |
