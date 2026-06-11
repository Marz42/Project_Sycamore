"""Resolve Sycamore local data directory paths."""

from __future__ import annotations

import os
from pathlib import Path

SYCA_HOME_ENV = "SYCA_HOME"
DEFAULT_HOME_DIRNAME = ".sycamore"
CONFIG_FILENAME = "config.toml"
DATABASE_FILENAME = "sycamore.db"
NODES_DIRNAME = "nodes"
REVIEWS_DIRNAME = "reviews"
ASSETS_DIRNAME = "assets"


def get_syca_home() -> Path:
    """Return the root data directory from SYCA_HOME or ~/.sycamore."""
    override = os.environ.get(SYCA_HOME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / DEFAULT_HOME_DIRNAME


def get_config_path(home: Path | None = None) -> Path:
    return (home or get_syca_home()) / CONFIG_FILENAME


def get_database_path(home: Path | None = None) -> Path:
    return (home or get_syca_home()) / DATABASE_FILENAME


def get_nodes_dir(home: Path | None = None) -> Path:
    return (home or get_syca_home()) / NODES_DIRNAME


def get_reviews_dir(home: Path | None = None) -> Path:
    return (home or get_syca_home()) / REVIEWS_DIRNAME


def get_assets_dir(home: Path | None = None) -> Path:
    return (home or get_syca_home()) / ASSETS_DIRNAME


def ensure_data_directories(home: Path | None = None) -> list[Path]:
    """Create standard data subdirectories. Returns paths that were created."""
    root = home or get_syca_home()
    created: list[Path] = []
    for relative in (NODES_DIRNAME, REVIEWS_DIRNAME, ASSETS_DIRNAME):
        target = root / relative
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(target)
    return created
