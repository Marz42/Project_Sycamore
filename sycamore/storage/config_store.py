"""Read and write local config.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_TEMPLATE = """\
[general]
default_editor = ""

[llm]
enabled = false
provider = ""

[freshness]
stale_after_days = 30
"""


def default_config_text() -> str:
    return DEFAULT_CONFIG_TEMPLATE


def write_default_config(config_path: Path) -> bool:
    """Write default config if missing. Returns True when a new file was created."""
    if config_path.exists():
        return False
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(default_config_text(), encoding="utf-8")
    return True


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)
