# AGENTS.md

## Global Workflow
Use a focused, evidence-first workflow for BARR.

For non-trivial tasks, always follow:
1. Understand context and constraints.
2. Plan a minimal executable slice.
3. Execute one scoped phase at a time.
4. Verify before claiming completion.

Efficiency rules:
- Keep updates concise and avoid repeating long docs.
- Prefer repository docs, code inspection, and tests over restating history.
- Avoid scope creep and unrelated rewrites.
- Do not mark complete without validation.

## Repo Priorities
Read these in order when relevant:
- [engineering/workflows/efficiency.md](engineering/workflows/efficiency.md)
- [progress/current-pilot-scope.md](progress/current-pilot-scope.md)
- [experiments/plans/week1-transition-probe.md](experiments/plans/week1-transition-probe.md)
- [research/framing/emnlp-2026-storyline.md](research/framing/emnlp-2026-storyline.md)

## AI Collaboration Defaults
- Codex is the default planner/executor/reporter.
- GitHub Copilot is for bounded local implementation after the plan is fixed.
- Claude review is only for high-risk architecture choices, major trade-offs, or unresolved conflicts.
- Minimize Claude calls: escalate only when risk or ambiguity is real.
- End each phase with concise progress, risks, and next minimal slice.

## Working Style
- Plan first for non-trivial tasks.
- Execute one scoped phase at a time.
- Verify before claiming completion.
- Keep updates concise.
- Prefer modifying the current narrowed pipeline over reviving old unused scaffolding.
- Avoid adding dependencies unless clearly necessary.
- Do not broaden scope without explicit justification.

## Current Pilot Focus
The current go/no-go question is not general benchmarking.
It is whether Qwen3-8B transition-point internal states can predict future biased answers on BBQ ambiguous samples well enough to justify BARR.

## Execution Defaults
- Use `conda activate gluo-barr` before running project commands.
- Use `/home/gluo/models` as the default model cache path.
- For small models, use one GPU per experiment and parallelize across GPUs.
- For larger models, allocate multiple GPUs per experiment and reduce concurrency accordingly.

## Research Log Skill
When I ask you to summarize today's experiments or generate a daily log,
follow the rules in `engineering/workflows/daily-research-log-skill.md`.
