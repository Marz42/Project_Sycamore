import os
from pathlib import Path

import pytest

from sycamore.core.init_service import initialize_sycamore
from sycamore.storage.database import get_schema_version, open_initialized_database
from sycamore.storage.schema import SCHEMA_VERSION
from sycamore.utils.paths import (
    ASSETS_DIRNAME,
    CONFIG_FILENAME,
    DATABASE_FILENAME,
    NODES_DIRNAME,
    REVIEWS_DIRNAME,
    SYCA_HOME_ENV,
)


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    return home


def test_initialize_creates_directories_config_and_database(syca_home: Path) -> None:
    result = initialize_sycamore(syca_home)

    assert result.home == syca_home
    assert result.created_config is True
    assert result.created_database is True
    assert (syca_home / CONFIG_FILENAME).exists()
    assert (syca_home / DATABASE_FILENAME).exists()
    assert (syca_home / NODES_DIRNAME).is_dir()
    assert (syca_home / REVIEWS_DIRNAME).is_dir()
    assert (syca_home / ASSETS_DIRNAME).is_dir()

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        assert get_schema_version(connection) == SCHEMA_VERSION
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table';"
            ).fetchall()
        }
        assert "capture_items" in tables
        assert "ability_nodes" in tables
        assert "capability_events" in tables
    finally:
        connection.close()


def test_initialize_is_idempotent(syca_home: Path) -> None:
    first = initialize_sycamore(syca_home)
    second = initialize_sycamore(syca_home)

    assert first.created_database is True
    assert second.created_database is False
    assert second.created_config is False
    assert not second.created_directories


def test_syca_home_env_is_respected(syca_home: Path) -> None:
    initialize_sycamore()
    assert os.environ[SYCA_HOME_ENV] == str(syca_home)
    assert (syca_home / DATABASE_FILENAME).exists()
