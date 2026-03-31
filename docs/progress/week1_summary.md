# Week 1 Summary

## Main findings

- Evaluated 1 model x dataset x language slices.
- Collected 1 paired counterfactual comparisons.
- Collected 0 candidate BF16-normal but quantized-biased cases.

## Pilot tables

- main_table.csv: results/main_table.csv
- per_language_table.csv: results/per_language_table.csv
- case_studies.jsonl: reports/case_studies.jsonl

## Notes

- Entropy / TECA fields are scaffolded but remain empty unless logits are exposed by the inference backend.
- OpenMBBQ is implemented as an open-style prompt variant with forced final A/B/C answer tags.
