from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.core.review_service import ReviewError, preview_review, run_review
from sycamore.models.enums import (
    CapabilityEventType,
    CaptureKind,
    ReviewStatus,
)
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import DATABASE_FILENAME, REVIEWS_DIRNAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote_with_mental_model(home: Path, cheat: str, title: str, mental_model: str) -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=cheat, home=home)
    result = promote_capture(capture.id, title=title, home=home)
    node_file = result.node_file
    text = node_file.read_text(encoding="utf-8")
    updated = text.replace(
        "用自己的话解释这个能力解决什么问题，以及背后的机制。",
        mental_model,
    )
    node_file.write_text(updated, encoding="utf-8")
    return result.node.id


def test_preview_review_shows_payload(syca_home: Path) -> None:
    node_id = _promote_with_mental_model(
        syca_home,
        "kubectl get pods",
        "我能查看 Kubernetes Pod",
        "Pod 是 Kubernetes 最小调度单元，kubectl get pods 列出当前命名空间实例。",
    )

    preview = preview_review(node_id, home=syca_home)

    assert preview.node.title.startswith("我能查看")
    assert "Pod 是 Kubernetes" in preview.payload.mental_model
    assert preview.payload.prompt_version == "p1-critique-v1"


def test_run_review_persists_review_run_and_event(syca_home: Path) -> None:
    node_id = _promote_with_mental_model(
        syca_home,
        "docker ps",
        "我能查看 Docker 容器",
        "docker ps 列出本机容器状态，含运行中与已退出实例。",
    )

    result = run_review(node_id, home=syca_home)

    assert result.node.review_status is ReviewStatus.CHALLENGED
    assert result.raw_output_file.exists()
    assert (syca_home / REVIEWS_DIRNAME / f"{result.review_run.id}.json").exists()

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        event = connection.execute(
            "SELECT type FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.REVIEW_COMPLETED.value),
        ).fetchone()
        assert event is not None
    finally:
        connection.close()


def test_review_rejects_placeholder_mental_model(syca_home: Path) -> None:
    capture = create_capture(kind=CaptureKind.NOTE, content="placeholder", home=syca_home)
    result = promote_capture(capture.id, title="我能整理笔记", home=syca_home)

    with pytest.raises(ReviewError, match="placeholder text"):
        preview_review(result.node.id, home=syca_home)


def test_review_cli_dry_run_and_run(syca_home: Path) -> None:
    node_id = _promote_with_mental_model(
        syca_home,
        "rg foo",
        "我能用 ripgrep 检索",
        "ripgrep 比 grep 更快，适合代码库递归搜索。",
    )
    runner = CliRunner()

    dry_result = runner.invoke(app, ["review", node_id, "--dry-run"])
    assert dry_result.exit_code == 0
    assert "Mental Model preview" in dry_result.output

    run_result = runner.invoke(app, ["review", node_id])
    assert run_result.exit_code == 0
    assert "Review completed" in run_result.output
