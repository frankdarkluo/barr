# Efficiency.md

> Purpose: reusable, low-overhead operating guidance for Codex across different repositories.
> Recommended use: keep this file as the durable source text, then load it through `AGENTS.md` and optionally turn parts of it into a Skill.

---

## Core objective

Use repository context efficiently, avoid repeated explanations, keep work scoped, and reduce unnecessary token use.

This guide is intentionally generic so it can be reused across many codebases.

---

## Operating defaults

1. Read repository guidance before asking for repeated context.
2. Prefer repository docs, code inspection, and existing tests over long conversational restatements.
3. Plan first for non-trivial tasks.
4. Execute one scoped step or one PR at a time.
5. Verify before claiming completion.
6. Keep outputs concise by default.
7. At each checkpoint, recommend the next reasoning effort briefly.

---

## Context priority

When starting work, use this priority order:

1. `AGENTS.md` and any more specific nested `AGENTS.md`
2. repository docs explicitly referenced by `AGENTS.md`
3. codebase structure, tests, build scripts, and configuration
4. direct user request in the current thread
5. older conversational context only if still relevant

If multiple docs overlap:
- prefer the most recent and most specific
- preserve compatible constraints from older docs
- surface real conflicts briefly instead of asking for broad restatement

---

## Low-token behavior rules

1. Do not restate long markdown docs back to the user.
2. Do not quote large blocks of repo documentation unless necessary.
3. Keep implementation updates short.
4. Prefer structured summaries over long prose.
5. Reuse stable repository guidance instead of asking the user to repeat it.
6. Ask clarifying questions only when a real blocker exists.
7. For long tasks, break work into explicit phases or PR-sized steps.
8. Do not implement unrelated features outside the current scope.

---

## Standard workflow

### Phase 1: understand
- read active `AGENTS.md`
- scan relevant docs
- inspect touched files
- identify constraints
- identify definition of done

### Phase 2: plan
For non-trivial tasks, first produce:
- phases or PR boundaries
- dependencies
- touched files
- migrations or config changes
- tests
- acceptance criteria
- open ambiguities

### Phase 3: execute
- execute exactly one scoped unit at a time
- stay within the approved scope
- avoid starting later phases early

### Phase 4: verify
Before claiming completion:
- run or describe relevant tests/checks
- confirm behavior changed as intended
- review for scope creep
- note remaining risks briefly

---

## Preferred response format

For implementation updates, return only:

1. what changed
2. files touched
3. tests added or updated
4. verification performed
5. remaining risks or ambiguities
6. recommended next reasoning effort

Keep each section brief.

---

## Reasoning-effort reminder rule

At every checkpoint, before proposing the next step, recommend the next reasoning effort in exactly this format:

Recommended next effort: <low|medium|high|extra high>
Why: <one short sentence>

Default guidance:
- low: tiny, well-scoped edits or simple follow-ups
- medium: most normal implementation steps and isolated PRs
- high: debugging, multi-file refactors, or validation-heavy work
- extra high: broad architecture, cross-cutting changes, or long agentic work

Do not over-explain the choice.

If the Codex surface uses `xhigh` instead of `extra high`, map them as equivalent.

---

## Testing and review defaults

When appropriate:
- write or update tests with the change
- run the smallest relevant checks first
- escalate to broader verification only when needed
- review the diff for regressions or risky assumptions before finishing

---

## Scope guardrails

Unless repository docs say otherwise:
- do not add new dependencies casually
- do not rewrite unrelated code
- do not broaden the task without explicit justification
- do not silently ignore failing verification
- do not mark work complete if tests or validation are missing

---

## Recommended repo pattern

Use this pattern for best results:

- `AGENTS.md` for auto-loaded working agreements
- `docs/` or repo markdown files for detailed project rules
- optional Skills for specialized reusable workflows
- concise prompts that point to repository files instead of repeating them

---

## Suggested short AGENTS.md wrapper

If you want to use this file through `AGENTS.md`, keep `AGENTS.md` short and point to this file:

```md
# AGENTS.md

## Global workflow
Follow the guidance in `Efficiency.md` before starting work.

## Repo-specific docs
Read the active project markdown docs before asking for repeated context.

## Working style
- Plan first for non-trivial tasks
- Execute one scoped step at a time
- Verify before completion
- Keep outputs concise
```

---

## Suggested prompt starter

Use this when beginning a task:

```text
Read AGENTS.md and any referenced project docs first.
Follow Efficiency.md-style behavior:
- plan first if the task is non-trivial
- execute one scoped step at a time
- verify before completion
- keep updates concise
- recommend the next reasoning effort at each checkpoint
```

---

## When to turn this into a Skill

Create a Skill only if you want Codex to invoke this workflow explicitly or implicitly across many repos.

Good candidates:
- code-review workflow
- deterministic debugging workflow
- PR finishing workflow
- execution-plan workflow
- repo onboarding workflow

Keep this file as the generic policy layer; use Skills for more specialized routines.

---

## Maintenance rule

When the same mistake happens twice:
- update `AGENTS.md` or the relevant project doc
- keep generic rules here
- keep repo-specific rules in the repo
- keep specialized workflows in Skills

This keeps guidance short, durable, and efficient.
