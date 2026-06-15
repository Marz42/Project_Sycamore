# Sycamore — Reasonix working knowledge

## Stack
- Python 3.12+
- uv (package manager, vendored via `uv.lock`)
- Typer (CLI framework) + Rich (terminal output)
- SQLite (`sycamore.db`) + Markdown files with YAML front matter
- DeepSeek (optional LLM review; mock by default)
- Build backend: hatchling
- pytest / ruff

## Layout
- `sycamore/cli/` — Typer commands; argument parsing + display only
- `sycamore/core/` — business logic / service orchestration
- `sycamore/models/` — domain dataclasses and enums
- `sycamore/review/` — LLM provider abstraction + prompt templates
- `sycamore/storage/` — SQLite repositories + Markdown read/write
- `sycamore/utils/` — pure utility functions (no project imports)
- `tests/` — pytest test files (`test_*.py`)

## Commands
| Action | Command |
|--------|---------|
| Run CLI | `uv run syca <command>` |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Dev install | `uv pip install -e .` |

## Conventions
- `from __future__ import annotations` in every Python file
- `snake_case` files/functions/vars; `PascalCase` classes; `StrEnum` for enums
- `@dataclass(frozen=True)` for domain models
- Full type annotations on all functions
- CLI imports from `core/`, never from `storage/` directly
- Tests: `tmp_path` + `monkeypatch` to set `SYCA_HOME_ENV`; `CliRunner` for CLI tests
- `VERSION` at project root is version authority (not `pyproject.toml`)
- `.env` loaded by `load_project_env()` before CLI app starts

## Watch out for
- Tests use temp `SYCA_HOME` — never read/write real `~/.sycamore/`
- Markdown node files are authoritative body; SQLite is a derived index
- CLI must delegate to `core/*_service` — no direct SQL or Markdown parsing in `cli/`
- LLM review is mock by default; needs `DEEPSEEK_API_KEY` in `.env` + `[llm]` config
- `VERSION` file is single source of truth for version bumps
