from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.doctor_service import run_doctor
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.core.query_service import query_cheatsheet
from sycamore.core.sync_service import sync_nodes
from sycamore.models.enums import CapabilityEventType, CaptureKind
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import DATABASE_FILENAME, NODES_DIRNAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote_cheat(home: Path, content: str, title: str) -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(capture.id, title=title, home=home)
    return result.node.id


def test_sync_updates_hashes_after_markdown_edit(syca_home: Path) -> None:
    node_id = _promote_cheat(syca_home, "rg foo", "我能用 ripgrep 检索")

    node_file = syca_home / NODES_DIRNAME / "ripgrep.md"
    if not node_file.exists():
        node_file = next((syca_home / NODES_DIRNAME).glob("*.md"))

    text = node_file.read_text(encoding="utf-8")
    updated = text.replace("rg foo", "rg bar")
    node_file.write_text(updated, encoding="utf-8")

    result = sync_nodes(home=syca_home)
    assert result.updated >= 1

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT content_hash FROM ability_nodes WHERE id = ?;",
            (node_id,),
        ).fetchone()
        assert row is not None
        event = connection.execute(
            "SELECT type FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.NODE_SYNCED.value),
        ).fetchone()
        assert event is not None
    finally:
        connection.close()

    report = run_doctor(home=syca_home)
    assert report.ok


def test_query_cheatsheet_finds_matching_node(syca_home: Path) -> None:
    node_id = _promote_cheat(syca_home, "docker ps -a", "我能查看 Docker 容器状态")

    matches = query_cheatsheet("docker", home=syca_home)

    assert len(matches) == 1
    assert matches[0].node.id == node_id
    assert "docker ps -a" in matches[0].cheatsheet

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        event = connection.execute(
            "SELECT type FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.CHEATSHEET_QUERIED.value),
        ).fetchone()
        assert event is not None
    finally:
        connection.close()


def test_doctor_reports_missing_markdown(syca_home: Path) -> None:
    _promote_cheat(syca_home, "ls -la", "我能列出目录")

    node_file = next((syca_home / NODES_DIRNAME).glob("*.md"))
    node_file.unlink()

    report = run_doctor(home=syca_home)

    assert not report.ok
    assert any(issue.code == "missing_markdown" for issue in report.issues)


def test_doctor_reports_orphan_markdown(syca_home: Path) -> None:
    orphan = syca_home / NODES_DIRNAME / "orphan.md"
    orphan.write_text(
        """\
---
id: "orphan-node"
slug: "orphan-node"
title: "孤儿节点"
claimedLevel: "L0"
createdAt: "2026-06-11T00:00:00+00:00"
updatedAt: "2026-06-11T00:00:00+00:00"
---

# 孤儿节点

## Cheatsheet

echo orphan
""",
        encoding="utf-8",
    )

    report = run_doctor(home=syca_home)

    assert not report.ok
    assert any(issue.code == "orphan_markdown" for issue in report.issues)


def test_query_sync_doctor_cli_flow(syca_home: Path) -> None:
    _promote_cheat(syca_home, "kubectl get pods", "我能查看 Kubernetes Pod")
    runner = CliRunner()

    sync_result = runner.invoke(app, ["sync"])
    assert sync_result.exit_code == 0
    assert "Synced" in sync_result.output

    query_result = runner.invoke(app, ["query", "kubectl", "--cheat"])
    assert query_result.exit_code == 0
    assert "kubectl get pods" in query_result.output

    doctor_result = runner.invoke(app, ["doctor"])
    assert doctor_result.exit_code == 0
    assert "No consistency issues" in doctor_result.output
