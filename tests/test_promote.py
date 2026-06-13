from pathlib import Path

import frontmatter
import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture, list_inbox
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import PromoteError, promote_capture
from sycamore.models.enums import (
    CapabilityEventType,
    CaptureKind,
    CaptureStatus,
    ClaimedLevel,
    ReviewStatus,
)
from sycamore.storage.capture_repository import list_inbox_captures
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import DATABASE_FILENAME, NODES_DIRNAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def test_promote_cheat_capture_creates_markdown_and_index(syca_home: Path) -> None:
    capture = create_capture(kind=CaptureKind.CHEAT, content="rg foo bar")

    result = promote_capture(
        capture.id,
        title="我能用 ripgrep 快速检索代码",
        domain="shell",
    )

    assert result.capture.status is CaptureStatus.PROMOTED
    assert result.capture.promoted_node_id == result.node.id
    assert result.node.title == "我能用 ripgrep 快速检索代码"
    assert result.node.domain == "shell"
    assert result.node.claimed_level is ClaimedLevel.L0
    assert result.node.review_status is ReviewStatus.NOT_REVIEWED
    assert result.node_file.exists()

    post = frontmatter.load(result.node_file)
    assert post["id"] == result.node.id
    assert post["slug"] == result.node.slug
    assert "rg foo bar" in post.content
    assert "## Cheatsheet" in post.content

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        event = connection.execute(
            """
            SELECT type, node_id, payload_json
            FROM capability_events
            WHERE capture_id = ? AND type = ?;
            """,
            (capture.id, CapabilityEventType.CAPTURE_PROMOTED.value),
        ).fetchone()
        assert event is not None
        assert event["node_id"] == result.node.id
        assert result.node.slug in event["payload_json"]
    finally:
        connection.close()


def test_promote_removes_capture_from_inbox(syca_home: Path) -> None:
    capture = create_capture(kind=CaptureKind.NOTE, content="awk delimiter pitfall")
    promote_capture(capture.id, title="我能解释 awk 字段分隔符的常见坑")

    assert list_inbox() == []


def test_promote_rejects_missing_capture(syca_home: Path) -> None:
    with pytest.raises(PromoteError, match="Capture not found"):
        promote_capture("missing-id")


def test_promote_rejects_already_promoted_capture(syca_home: Path) -> None:
    capture = create_capture(kind=CaptureKind.NOTE, content="once only")
    promote_capture(capture.id, title="我能整理这条笔记")

    with pytest.raises(PromoteError, match="cannot be promoted"):
        promote_capture(capture.id, title="重复升格")


def test_promote_generates_unique_slug_on_collision(syca_home: Path) -> None:
    first = create_capture(kind=CaptureKind.NOTE, content="first")
    second = create_capture(kind=CaptureKind.NOTE, content="second")

    first_result = promote_capture(first.id, title="Shell Basics")
    second_result = promote_capture(second.id, title="Shell Basics")

    assert first_result.node.slug == "shell-basics"
    assert second_result.node.slug == "shell-basics-2"
    assert first_result.node_file.exists()
    assert second_result.node_file.exists()


def test_promote_cli_flow(syca_home: Path) -> None:
    capture = create_capture(kind=CaptureKind.CHEAT, content="docker ps -a")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "promote",
            capture.id,
            "--title",
            "我能查看 Docker 容器状态",
            "--domain",
            "docker",
        ],
    )

    assert result.exit_code == 0
    assert "Promoted" in result.output
    assert "我能查看 Docker 容器状态" in result.output
    assert (syca_home / NODES_DIRNAME).exists()


def test_promote_without_id_promotes_latest(syca_home: Path) -> None:
    create_capture(kind=CaptureKind.NOTE, content="older")
    latest = create_capture(kind=CaptureKind.CHEAT, content="kubectl get pods")

    result = promote_capture()

    assert result.capture.id == latest.id
    assert "kubectl get pods" in result.node_file.read_text(encoding="utf-8")


def test_promote_latest_flag_promotes_newest_inbox_item(syca_home: Path) -> None:
    create_capture(kind=CaptureKind.NOTE, content="older")
    latest = create_capture(kind=CaptureKind.CHEAT, content="git status")

    result = promote_capture(latest=True)

    assert result.capture.id == latest.id


def test_promote_index_selects_inbox_row(syca_home: Path) -> None:
    first = create_capture(kind=CaptureKind.NOTE, content="first")
    create_capture(kind=CaptureKind.CHEAT, content="second")

    result = promote_capture(index=2)

    assert result.capture.content == "first"
    assert result.capture.id == first.id


def test_promote_accepts_unique_uuid_prefix(syca_home: Path) -> None:
    capture = create_capture(kind=CaptureKind.LINK, content="https://example.com", source="https://example.com")

    result = promote_capture(capture.id[:8], title="我能查阅该资料")

    assert result.capture.id == capture.id


def test_promote_rejects_ambiguous_uuid_prefix(syca_home: Path) -> None:
    create_capture(kind=CaptureKind.NOTE, content="a")
    create_capture(kind=CaptureKind.NOTE, content="b")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        items = list_inbox_captures(connection)
        for length in range(1, 9):
            prefix = items[0].id[:length]
            matches = [item for item in items if item.id.startswith(prefix)]
            if len(matches) >= 2:
                with pytest.raises(PromoteError, match="multiple inbox items"):
                    promote_capture(prefix)
                return
        pytest.skip("Could not construct ambiguous prefix with two inbox items.")
    finally:
        connection.close()


def test_promote_empty_inbox_without_selector_fails(syca_home: Path) -> None:
    with pytest.raises(PromoteError, match="Inbox is empty"):
        promote_capture()


def test_promote_cli_without_id(syca_home: Path) -> None:
    create_capture(kind=CaptureKind.CHEAT, content="uv run pytest")
    runner = CliRunner()

    result = runner.invoke(app, ["promote", "--title", "我能运行项目测试"])

    assert result.exit_code == 0
    assert "Promoted" in result.output


def test_inbox_shows_index_and_short_id(syca_home: Path) -> None:
    capture = create_capture(kind=CaptureKind.NOTE, content="hello inbox")
    runner = CliRunner()

    result = runner.invoke(app, ["inbox"])

    assert result.exit_code == 0
    assert "1" in result.output
    assert capture.id[:8] in result.output
