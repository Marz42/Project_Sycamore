# Sycamore

Sycamore is a local-first CLI tool for capability calibration and recovery.

It is designed for cross-domain learners who want a low-friction way to capture useful fragments during real work, then gradually promote the important ones into structured ability notes.

## Product Loop

```text
Capture -> Clarify -> Encode -> Challenge -> Practice -> Recover
```

P0 focuses on the reliable local loop:

```bash
syca init
syca capture --cheat "awk '{print $1}' access.log | sort | uniq -c"
syca capture --note "awk field separators caused trouble today"
syca inbox
syca promote <capture-id>
syca query "awk" --cheat
syca sync
syca doctor
```

## Current Stage

The project is entering P0 construction.

Current priorities:

- Python CLI project skeleton.
- Local data directory and SQLite schema.
- CaptureItem and Inbox flow.
- Promotion from CaptureItem to Markdown AbilityNode.
- Cheatsheet query.
- Markdown/SQLite sync and doctor checks.

## Architecture

Sycamore is intentionally conservative:

- Python 3.12+
- uv
- Typer
- Rich
- SQLite through `sqlite3` repository wrappers
- Markdown with YAML Front Matter
- pytest

The project explicitly does not start with Web, ORM, RAG, plugins, background daemons, or a long-running API service.

## Memory Bank

Project context is maintained in `memory_bank/`.

Key files:

- `memory_bank/project-brief.md`
- `memory_bank/architecture.md`
- `memory_bank/data-contracts.md`
- `memory_bank/conventions.md`
- `memory_bank/active-task.md`
- `memory_bank/roadmap.md`
- `memory_bank/progress.md`

## Status

No installable package is available yet. See `memory_bank/roadmap.md` for the current implementation plan.

## License

This repository currently keeps the inherited MPL 2.0 license from its project base. Revisit licensing before public release if needed.
