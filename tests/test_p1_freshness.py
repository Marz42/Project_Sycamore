from datetime import UTC, datetime
from pathlib import Path

import frontmatter
import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.level_service import LevelError, set_claimed_level
from sycamore.core.practice_service import PracticeError, log_practice
from sycamore.core.promote_service import promote_capture
from sycamore.core.status_service import list_stale_nodes
from sycamore.models.enums import CapabilityEventType, CaptureKind, ClaimedLevel
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote_node(home: Path, content: str, title: str) -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(capture.id, title=title, home=home)
    return result.node.id


def test_log_practice_appends_entry_and_event(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "rg foo", "我能用 ripgrep 检索")

    result = log_practice(
        node_id,
        scenario="code search",
        action="rg pattern src/",
        result="found matches",
        home=syca_home,
    )

    post = frontmatter.load(result.node_file)
    assert "rg pattern src/" in post.content
    assert "code search" in post.content

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        event = connection.execute(
            "SELECT type FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.PRACTICE_LOGGED.value),
        ).fetchone()
        assert event is not None
    finally:
        connection.close()


def test_log_practice_requires_fields(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "ls", "我能列出目录")

    with pytest.raises(PracticeError, match="at least one"):
        log_practice(node_id, home=syca_home)


def test_set_claimed_level_updates_markdown_and_event(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "docker ps", "我能查看 Docker 容器")

    result = set_claimed_level(node_id, ClaimedLevel.L2, home=syca_home)

    assert result.new_level is ClaimedLevel.L2
    post = frontmatter.load(syca_home / result.node.node_path)
    assert post["claimedLevel"] == "L2"

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT claimed_level FROM ability_nodes WHERE id = ?;",
            (node_id,),
        ).fetchone()
        assert row["claimed_level"] == "L2"
        event = connection.execute(
            "SELECT type FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.MANUAL_LEVEL_CHANGED.value),
        ).fetchone()
        assert event is not None
    finally:
        connection.close()


def test_set_same_level_is_rejected(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "kubectl get pods", "我能查看 Pod")

    with pytest.raises(LevelError, match="already has"):
        set_claimed_level(node_id, ClaimedLevel.L0, home=syca_home)


def test_list_stale_nodes_uses_activity_threshold(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "git status", "我能查看 Git 状态")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        connection.execute(
            "UPDATE ability_nodes SET created_at = ? WHERE id = ?;",
            ("2020-01-01T00:00:00+00:00", node_id),
        )
        connection.commit()
    finally:
        connection.close()

    report = list_stale_nodes(home=syca_home, stale_after_days=30)
    assert any(item.node.id == node_id for item in report.nodes)


def test_practice_refreshes_freshness(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "make build", "我能构建项目")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        connection.execute(
            "UPDATE ability_nodes SET created_at = ? WHERE id = ?;",
            ("2020-01-01T00:00:00+00:00", node_id),
        )
        connection.commit()
    finally:
        connection.close()

    assert any(
        item.node.id == node_id
        for item in list_stale_nodes(home=syca_home, stale_after_days=30).nodes
    )

    log_practice(node_id, note="rebuilt locally", home=syca_home)

    fresh_report = list_stale_nodes(
        home=syca_home,
        stale_after_days=30,
        now=datetime.now(UTC),
    )
    assert not any(item.node.id == node_id for item in fresh_report.nodes)


def test_practice_status_level_cli_flow(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "uv run pytest", "我能运行测试")
    runner = CliRunner()

    practice_result = runner.invoke(
        app,
        ["practice", node_id, "--note", "all tests passed"],
    )
    assert practice_result.exit_code == 0

    level_result = runner.invoke(app, ["level", "set", node_id, "L1"])
    assert level_result.exit_code == 0
    assert "L0 -> L1" in level_result.output

    status_result = runner.invoke(app, ["status", "--stale"])
    assert status_result.exit_code == 0
