# BARR Docs README

This folder is organized for long-term maintenance and Obsidian-style navigation.

The guiding rule is simple: group notes by purpose, not by creation date.

## Structure

```text
docs/
  README.md
  index.md
  engineering/
    workflows/
  research/
    framing/
    reviews/
  experiments/
    plans/
    results/
  progress/
    current-pilot-scope.md
    daily/
    weekly/
  product/
  ux/
  archive/
```

## What Goes Where

- `engineering/`: workflow rules, collaboration rules, note-writing skills, and operational conventions.
- `research/`: thesis framing, paper storyline, method claims, and review-style synthesis notes.
- `experiments/`: executable plans plus result notes grouped by experiment or slice.
- `progress/`: the living project state.
  - `current-pilot-scope.md`: the active go/no-go question and current operating scope.
  - `daily/`: dated research logs.
  - `weekly/`: weekly checkpoints and summaries.
- `product/`: reserved for future deployment-facing or user-facing product notes.
- `ux/`: reserved for future interface, flow, or experience notes.
- `archive/`: superseded notes kept for provenance after consolidation or restructuring.

## Naming Rules

- Use concise, stable, English-first filenames in `kebab-case`.
- Use dates only for time-based notes:
  - daily logs: `YYYY-MM-DD.md`
  - weekly summaries: `YYYY-MM-DD-weekly.md`
- Prefer concept names over meeting-style names.
- If a note is replaced by a cleaner consolidated note, move the old note to `archive/` instead of silently deleting it.

## Obsidian Linking Rules

- Add a short `Related notes` section near the top of important notes.
- Prefer linking to concept notes and summary notes, not only to folders.
- Keep filenames stable once a note becomes a hub.
- When creating a Chinese companion note, keep the same basename and add a language suffix:
  - `note-name.md`
  - `note-name.zh.md`
- If a note is bilingual but short, keep both languages in one note and add explicit cross-links to the relevant experiment or framing note.

## Maintenance Rules

- If a note explains project direction, it belongs in `research/` or `progress/`, not in `daily/`.
- If a note contains frozen numbers or experiment outputs, it belongs in `experiments/results/`.
- If a note describes how to run or maintain the project, it belongs in `engineering/workflows/`.
- If a daily note contains a durable conclusion, promote that conclusion into `research/`, `experiments/results/`, or `progress/current-pilot-scope.md`.

## Current Reading Path

If you are new to this repo, start here:

1. [Docs Index](index.md)
2. [Current Pilot Scope](progress/current-pilot-scope.md)
3. [BARR Mainline Claim](research/framing/barr-mainline.md)
4. [EMNLP 2026 Storyline](research/framing/emnlp-2026-storyline.md)
