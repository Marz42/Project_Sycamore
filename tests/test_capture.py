from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture, list_inbox
from sycamore.core.init_service import initialize_sycamore
from sycamore.models.enums import CaptureKind, CaptureStatus, CapabilityEventType
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def test_create_capture_persists_item_and_event(syca_home: Path) -> None:
    item = create_capture(kind=CaptureKind.CHEAT, content="awk '{print $1}' access.log")

    assert item.kind is CaptureKind.CHEAT
    assert item.status is CaptureStatus.INBOX
    assert item.content.startswith("awk")

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        event = connection.execute(
            "SELECT type FROM capability_events WHERE capture_id = ?;",
            (item.id,),
        ).fetchone()
        assert event is not None
        assert event["type"] == CapabilityEventType.CAPTURE_CREATED.value
    finally:
        connection.close()


def test_list_inbox_returns_only_inbox_items(syca_home: Path) -> None:
    create_capture(kind=CaptureKind.NOTE, content="first")
    create_capture(kind=CaptureKind.LINK, content="https://example.com", source="https://example.com")

    items = list_inbox()
    assert len(items) == 2
    assert all(item.status is CaptureStatus.INBOX for item in items)


def test_capture_cli_requires_init(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    home = tmp_path / "uninitialized"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    runner = CliRunner()

    result = runner.invoke(app, ["capture", "--note", "not initialized yet"])

    assert result.exit_code == 1
    assert "Run `syca init` first" in result.output


def test_capture_and_inbox_cli_flow(syca_home: Path) -> None:
    runner = CliRunner()

    capture_result = runner.invoke(
        app,
        ["capture", "--cheat", "rg foo"],
    )
    assert capture_result.exit_code == 0
    assert "Captured" in capture_result.output

    inbox_result = runner.invoke(app, ["inbox"])
    assert inbox_result.exit_code == 0
    assert "rg foo" in inbox_result.output
