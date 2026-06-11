"""Initialize local Sycamore data directory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sycamore.storage.config_store import write_default_config
from sycamore.storage.database import connect, initialize_schema
from sycamore.utils.paths import (
    ensure_data_directories,
    get_config_path,
    get_database_path,
    get_syca_home,
)


@dataclass(frozen=True)
class InitResult:
    home: Path
    created_directories: tuple[Path, ...]
    created_config: bool
    created_database: bool


def initialize_sycamore(home: Path | None = None) -> InitResult:
    root = home or get_syca_home()
    root.mkdir(parents=True, exist_ok=True)

    created_directories = tuple(ensure_data_directories(root))
    created_config = write_default_config(get_config_path(root))

    database_path = get_database_path(root)
    connection = connect(database_path)
    try:
        created_database = initialize_schema(connection)
    finally:
        connection.close()

    return InitResult(
        home=root,
        created_directories=created_directories,
        created_config=created_config,
        created_database=created_database,
    )
