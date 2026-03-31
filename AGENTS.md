# AGENTS.md

## Global Workflow
Follow [Efficiency.md](/home/gluo/barr/Efficiency.md) before starting non-trivial work.

## Repo Priorities
Read these in order when relevant:
- [Efficiency.md](/home/gluo/barr/Efficiency.md)
- [PROGRESS.md](/home/gluo/barr/PROGRESS.md)
- [week1_transition_probe_codex_plan.md](/home/gluo/barr/week1_transition_probe_codex_plan.md)

## Working Style
- Plan first for non-trivial tasks.
- Execute one scoped phase at a time.
- Verify before claiming completion.
- Keep updates concise.
- Prefer modifying the current narrowed pipeline over reviving old unused scaffolding.

## Current Pilot Focus
The current go/no-go question is not general benchmarking.
It is whether Qwen3-8B transition-point internal states can predict future biased answers on BBQ ambiguous samples well enough to justify BARR.

## Execution Defaults
- Use `conda activate gluo-barr` before running project commands.
- Use `/home/gluo/models` as the default model cache path.
- For small models, use one GPU per experiment and parallelize across GPUs.
- For larger models, allocate multiple GPUs per experiment and reduce concurrency accordingly.
