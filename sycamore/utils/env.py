"""Load environment variables from local .env files."""

from __future__ import annotations

import os
from pathlib import Path

from sycamore.utils.paths import SYCA_HOME_ENV, get_syca_home


def _apply_env_line(line: str) -> None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return
    if stripped.startswith("export "):
        stripped = stripped.removeprefix("export ").strip()
    if "=" not in stripped:
        return
    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    if key and key not in os.environ:
        os.environ[key] = value


def load_dotenv_file(path: Path) -> bool:
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        _apply_env_line(line)
    return True


def load_project_env(*, cwd: Path | None = None) -> tuple[Path, ...]:
    """Load .env without overriding variables already in the process environment."""
    loaded: list[Path] = []
    candidates = [Path.cwd() / ".env"]
    if cwd is not None:
        candidates.insert(0, cwd / ".env")

    syca_home_env = os.environ.get(SYCA_HOME_ENV)
    if syca_home_env:
        candidates.append(Path(syca_home_env).expanduser() / ".env")
    else:
        candidates.append(get_syca_home() / ".env")

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if load_dotenv_file(resolved):
            loaded.append(resolved)
    return tuple(loaded)
