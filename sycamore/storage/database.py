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


_MIGRATIONS: dict[int, str] = {
    1: "ALTER TABLE ability_nodes ADD COLUMN node_type TEXT NOT NULL DEFAULT 'capability';",
    2: (
        "CREATE TABLE IF NOT EXISTS node_scheduler_state ("
        "node_id TEXT PRIMARY KEY, stability REAL NOT NULL DEFAULT 0,"
        "difficulty REAL NOT NULL DEFAULT 5.0, due_at TEXT, last_review_at TEXT,"
        "last_rating INTEGER, review_count INTEGER DEFAULT 0, lapse_count INTEGER DEFAULT 0,"
        "FOREIGN KEY (node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE"
        ");"
    ),
    3: (
        # Recreate capability_events with expanded type CHECK (adds transfer_* types)
        "CREATE TABLE capability_events_new ("
        "id TEXT PRIMARY KEY, node_id TEXT, capture_id TEXT,"
        "type TEXT NOT NULL CHECK (type IN ("
        "'capture_created','capture_promoted','practice_logged','cheatsheet_queried',"
        "'review_completed','recovery_passed','recovery_failed','manual_level_changed',"
        "'node_synced','transfer_success','transfer_partial','transfer_fail')),"
        "payload_json TEXT, created_at TEXT NOT NULL,"
        "FOREIGN KEY (node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE,"
        "FOREIGN KEY (capture_id) REFERENCES capture_items(id) ON DELETE CASCADE);"
        "INSERT INTO capability_events_new SELECT * FROM capability_events;"
        "DROP TABLE capability_events;"
        "ALTER TABLE capability_events_new RENAME TO capability_events;"
    ),
}


def _migrate(connection: sqlite3.Connection, current_version: int) -> int:
    """Run migrations sequentially from current_version to SCHEMA_VERSION."""
    for v in range(current_version, SCHEMA_VERSION):
        sql = _MIGRATIONS.get(v + 1)
        if sql is None:
            raise DatabaseError(f"No migration defined for schema v{v} → v{v + 1}.")
        connection.execute(sql)
    connection.execute("UPDATE schema_version SET version = ?;", (SCHEMA_VERSION,))
    connection.commit()
    return SCHEMA_VERSION


def initialize_schema(connection: sqlite3.Connection) -> bool:
    """Apply schema statements. Returns True if this call initialized a new database."""
    existing_version = get_schema_version(connection)
    if existing_version is not None:
        if existing_version == SCHEMA_VERSION:
            return False
        if existing_version < SCHEMA_VERSION:
            _migrate(connection, existing_version)
            return False
        raise DatabaseError(
            f"Unsupported schema version {existing_version}; expected {SCHEMA_VERSION}."
        )

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
