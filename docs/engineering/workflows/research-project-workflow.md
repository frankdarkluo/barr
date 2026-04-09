# Research Project Workflow

## Related notes
- [Docs Structure Rules](../../README.md)
- [Docs Index](../../index.md)
- [Current Pilot Scope](../../progress/current-pilot-scope.md)
- [Daily Research Log Skill](daily-research-log-skill.md)

## Purpose

This workflow keeps the BARR docs set clean, navigable, and useful for long-running research work.

The aim is not to preserve every markdown file forever.
The aim is to preserve the project memory in a way that supports:

- current execution
- paper framing
- experiment traceability
- Obsidian graph navigation

## Core Rules

1. Group notes by purpose, not by creation date.
2. Promote durable conclusions out of daily logs.
3. Merge overlapping notes into a clearer hub note when the overlap is obvious.
4. Archive superseded notes instead of silently deleting them.
5. Keep filenames stable once a note becomes a navigation hub.

## Folder Routing

### `docs/research/`

Use for:

- thesis framing
- method claims
- storyline notes
- high-level review or synthesis notes

### `docs/experiments/plans/`

Use for:

- protocol definitions
- acceptance criteria
- go/no-go rules
- planned experiment slices

### `docs/experiments/results/`

Use for:

- frozen result tables
- slice summaries
- result consolidations
- experiment-specific conclusions

### `docs/progress/`

Use for:

- current project scope
- daily logs
- weekly summaries

### `docs/engineering/workflows/`

Use for:

- collaboration instructions
- documentation rules
- reusable writing skills
- process and maintenance guidance

## Daily and Weekly Rules

- Daily session notes go in `docs/progress/daily/` using `YYYY-MM-DD.md`.
- Weekly summaries go in `docs/progress/weekly/` using `YYYY-MM-DD-weekly.md`.
- Weekly notes should summarize stable movement, not repeat every minor event.
- If a daily note creates a durable conclusion, move that conclusion into:
  - `docs/research/`
  - `docs/experiments/results/`
  - or `docs/progress/current-pilot-scope.md`

## Merge and Archive Rules

- If two or more notes tell the same story with slightly different protocol snapshots, create one cleaner main note.
- Move the older source notes into `docs/archive/`.
- In the new main note, link back to the archived source notes for provenance.

## Obsidian Rules

- Use concise, readable filenames in `kebab-case`.
- Add a `Related notes` section near the top of important notes.
- Prefer links between framing, plans, results, and progress rather than relying on folder layout alone.
- If a Chinese companion note exists, use the same basename with a language suffix.

## Recommended Maintenance Cadence

1. Update `current-pilot-scope.md` when the actual project focus changes.
2. Update a daily log after a meaningful work session.
3. Update the weekly note when the week has enough stable movement to summarize.
4. Update research framing notes only when the claims or narrative should change.
