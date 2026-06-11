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
