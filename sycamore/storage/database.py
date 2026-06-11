"""SQLite connection and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from sycamore.storage.schema import SCHEMA_STATEMENTS, SCHEMA_VERSION


class DatabaseError(Exception):
    """Raised when SQLite operations fail."""


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def get_schema_version(connection: sqlite3.Connection) -> int | None:
    try:
        row = connection.execute("SELECT version FROM schema_version LIMIT 1;").fetchone()
    except sqlite3.OperationalError:
        return None
    if row is None:
        return None
    return int(row["version"])


def initialize_schema(connection: sqlite3.Connection) -> bool:
    """Apply schema statements. Returns True if this call initialized a new database."""
    existing_version = get_schema_version(connection)
    if existing_version is not None:
        if existing_version != SCHEMA_VERSION:
            raise DatabaseError(
                f"Unsupported schema version {existing_version}; expected {SCHEMA_VERSION}."
            )
        return False

    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    connection.execute("INSERT INTO schema_version (version) VALUES (?);", (SCHEMA_VERSION,))
    connection.commit()
    return True


def open_initialized_database(database_path: Path) -> sqlite3.Connection:
    if not database_path.exists():
        raise DatabaseError(
            f"Database not found at {database_path}. Run `syca init` first."
        )
    connection = connect(database_path)
    version = get_schema_version(connection)
    if version is None:
        raise DatabaseError(
            f"Database at {database_path} is missing schema metadata. Run `syca init`."
        )
    if version != SCHEMA_VERSION:
        raise DatabaseError(
            f"Unsupported schema version {version}; expected {SCHEMA_VERSION}."
        )
    return connection
