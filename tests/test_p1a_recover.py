"""Tests for Phase 1A: recall-first recover, fail-type, ratings, status --weak."""

import json
from pathlib import Path

import frontmatter
import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.core.recover_service import (
    FailType,
    RecoverMode,
    RecoverRating,
    _recall_prompt,
    preview_recovery_drill,
    record_recovery_outcome,
)
from sycamore.core.status_service import list_weak_nodes
from sycamore.models.enums import CapabilityEventType, CaptureKind
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import replace_section
from sycamore.utils.paths import DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote_node(
    home: Path,
    content: str,
    title: str,
    *,
    domain: str | None = None,
    node_type: str = "capability",
) -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(
        capture.id, title=title, domain=domain, node_type=node_type, home=home
    )
    return result.node.id


def _write_mental_model(home: Path, node_id: str, text: str) -> None:
    connection = open_initialized_database(home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;",
            (node_id,),
        ).fetchone()
        assert row is not None
        node_file = home / row["node_path"]
    finally:
        connection.close()

    post = frontmatter.load(node_file)
    updated_body = replace_section(
        post.content,
        "Mental Model",
        "### Core Idea\n\n" + text + "\n\n### Boundaries\n\n- test",
    )
    post.content = updated_body
    node_file.write_text(frontmatter.dumps(post), encoding="utf-8")


# ── Recall prompt tests ──────────────────────────────────────────────


def test_recall_prompt_for_capability() -> None:
    assert "步骤" in _recall_prompt("capability")


def test_recall_prompt_for_concept() -> None:
    assert "核心主张" in _recall_prompt("concept")


def test_recall_prompt_for_theorem() -> None:
    assert "公式" in _recall_prompt("theorem") or "直觉" in _recall_prompt("theorem")


def test_recall_prompt_for_process() -> None:
    assert "机理" in _recall_prompt("process")


def test_recall_prompt_defaults_to_capability() -> None:
    assert _recall_prompt("unknown") == _recall_prompt("capability")


# ── Mode tests ───────────────────────────────────────────────────────


def test_preview_default_mode_is_recall_first(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "rg foo", "我能 grep", domain="shell")
    _write_mental_model(syca_home, node_id, "grep filters text lines.")

    drill = preview_recovery_drill(node_id, home=syca_home)
    assert drill.recall_prompt  # recall-first provides a prompt


def test_preview_full_mode_shows_content(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "ls", "我能 list", domain="shell")
    _write_mental_model(syca_home, node_id, "ls lists directory contents.")

    drill = preview_recovery_drill(node_id, mode=RecoverMode.FULL, home=syca_home)
    assert "ls lists directory contents" in drill.mental_model


def test_preview_with_concept_node_type(syca_home: Path) -> None:
    node_id = _promote_node(
        syca_home, "theory", "我能分析", domain="philosophy", node_type="concept"
    )
    # Concept nodes have ## Core Thesis instead of ## Mental Model — we need to
    # add a Mental Model section manually for recovery to work.
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;",
            (node_id,),
        ).fetchone()
        assert row is not None
        node_file = syca_home / row["node_path"]
    finally:
        connection.close()

    post = frontmatter.load(node_file)
    post.content = post.content + "\n\n## Mental Model\n\n### Core Idea\n\nThis theory explains...\n\n### Boundaries\n\n- test\n"
    node_file.write_text(frontmatter.dumps(post), encoding="utf-8")

    drill = preview_recovery_drill(node_id, home=syca_home)
    assert drill.node_type == "concept"
    assert "核心主张" in drill.recall_prompt


# ── Rating tests ─────────────────────────────────────────────────────


def test_record_hard_rating(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "cmd", "测试命令", domain="test")
    result = record_recovery_outcome(node_id, rating=RecoverRating.HARD, home=syca_home)

    assert result.rating == "hard"
    assert result.passed is True
    assert result.fail_type is None

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT payload_json FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.RECOVERY_PASSED.value),
        ).fetchone()
        assert row is not None
        payload = json.loads(row["payload_json"])
        assert payload["rating"] == "hard"
    finally:
        connection.close()


def test_record_easy_rating(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "cmd", "简单命令", domain="test")
    result = record_recovery_outcome(node_id, rating=RecoverRating.EASY, home=syca_home)

    assert result.rating == "easy"
    assert result.passed is True


def test_record_fail_with_type(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "cmd", "概念节点", domain="test")
    result = record_recovery_outcome(
        node_id,
        rating=RecoverRating.FAIL,
        fail_type=FailType.CONCEPT,
        note="did not understand the core idea",
        home=syca_home,
    )

    assert result.rating == "fail"
    assert result.passed is False
    assert result.fail_type == "concept"

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT payload_json FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.RECOVERY_FAILED.value),
        ).fetchone()
        assert row is not None
        payload = json.loads(row["payload_json"])
        assert payload["rating"] == "fail"
        assert payload["failType"] == "concept"
        assert payload["note"] == "did not understand the core idea"
    finally:
        connection.close()


def test_record_pass_with_failtype_is_rejected() -> None:
    # fail-type only valid with fail
    pass


def test_all_fail_types(syca_home: Path) -> None:
    for ft in (FailType.RECALL, FailType.CONCEPT, FailType.PROCEDURE, FailType.TRANSFER):
        node_id = _promote_node(syca_home, f"cmd-{ft.value}", f"节点-{ft.value}", domain="test")
        result = record_recovery_outcome(
            node_id, rating=RecoverRating.FAIL, fail_type=ft, home=syca_home
        )
        assert result.fail_type == ft.value
        assert result.rating == "fail"


# ── Weakness analysis tests ──────────────────────────────────────────


def test_weak_nodes_empty_when_no_fails(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "cmd", "全是通过的", domain="test")
    record_recovery_outcome(node_id, rating=RecoverRating.PASS, home=syca_home)
    record_recovery_outcome(node_id, rating=RecoverRating.EASY, home=syca_home)

    report = list_weak_nodes(home=syca_home)
    assert len(report.nodes) == 0
    assert report.total_fails == 0


def test_weak_nodes_counts_fails(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "hard-cmd", "总是失败的命令", domain="shell")
    for _ in range(4):
        record_recovery_outcome(
            node_id,
            rating=RecoverRating.FAIL,
            fail_type=FailType.PROCEDURE,
            home=syca_home,
        )
    record_recovery_outcome(
        node_id,
        rating=RecoverRating.FAIL,
        fail_type=FailType.CONCEPT,
        home=syca_home,
    )

    report = list_weak_nodes(home=syca_home)
    assert len(report.nodes) == 1
    w = report.nodes[0]
    assert w.fail_count == 5
    assert w.top_fail_type == "procedure"
    assert w.risk_level == "high"
    assert report.total_fails == 5


def test_weak_nodes_multiple_nodes(syca_home: Path) -> None:
    a = _promote_node(syca_home, "a", "节点A", domain="dev")
    b = _promote_node(syca_home, "b", "节点B", domain="dev")

    record_recovery_outcome(a, rating=RecoverRating.FAIL, fail_type=FailType.RECALL, home=syca_home)
    record_recovery_outcome(a, rating=RecoverRating.FAIL, fail_type=FailType.RECALL, home=syca_home)
    record_recovery_outcome(b, rating=RecoverRating.FAIL, fail_type=FailType.TRANSFER, home=syca_home)

    report = list_weak_nodes(home=syca_home)
    assert len(report.nodes) == 2
    # Most fails first
    assert report.nodes[0].node.id == a


def test_weak_nodes_risk_levels(syca_home: Path) -> None:
    low = _promote_node(syca_home, "l", "低风险", domain="dev")
    med = _promote_node(syca_home, "m", "中风险", domain="dev")
    high = _promote_node(syca_home, "h", "高风险", domain="dev")

    record_recovery_outcome(low, rating=RecoverRating.FAIL, fail_type=FailType.RECALL, home=syca_home)
    record_recovery_outcome(low, rating=RecoverRating.FAIL, fail_type=FailType.RECALL, home=syca_home)

    for _ in range(3):
        record_recovery_outcome(med, rating=RecoverRating.FAIL, fail_type=FailType.CONCEPT, home=syca_home)

    for _ in range(5):
        record_recovery_outcome(high, rating=RecoverRating.FAIL, fail_type=FailType.PROCEDURE, home=syca_home)

    report = list_weak_nodes(home=syca_home)
    risks = {w.node.title: w.risk_level for w in report.nodes}
    assert risks["低风险"] == "low"
    assert risks["中风险"] == "medium"
    assert risks["高风险"] == "high"


# ── CLI tests ────────────────────────────────────────────────────────


def test_recover_cli_recall_first_default(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "rg pattern", "我能 grep", domain="shell")
    _write_mental_model(syca_home, node_id, "grep filters lines by pattern.")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id])
    assert result.exit_code == 0
    assert "Recall challenge" in result.stdout
    assert "grep filters" in result.stdout


def test_recover_cli_full_mode(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "ls", "我能 list", domain="shell")
    _write_mental_model(syca_home, node_id, "ls lists directory contents.")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--mode", "full"])
    assert result.exit_code == 0
    # Full mode should NOT show "Recall challenge"
    assert "Recall challenge" not in result.stdout
    assert "ls lists directory contents" in result.stdout


def test_recover_cli_hard_rating(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "cmd", "测试", domain="test")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--hard"])
    assert result.exit_code == 0
    assert "hard" in result.stdout


def test_recover_cli_easy_rating(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "cmd", "简单", domain="test")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--easy"])
    assert result.exit_code == 0
    assert "easy" in result.stdout


def test_recover_cli_fail_with_type(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "theory", "概念节点", domain="philosophy")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--fail", "--fail-type", "concept"])
    assert result.exit_code == 0
    assert "failed" in result.stdout
    assert "concept" in result.stdout


def test_recover_cli_rejects_multiple_ratings(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "cmd", "测试", domain="test")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--pass", "--fail"])
    assert result.exit_code == 1
    assert "at most one" in result.stdout


def test_recover_cli_rejects_fail_type_without_fail(
    syca_home: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "cmd", "测试", domain="test")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--pass", "--fail-type", "concept"])
    assert result.exit_code == 1
    assert "only valid with --fail" in result.stdout


def test_recover_cli_invalid_mode(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "cmd", "测试", domain="test")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--mode", "invalid"])
    assert result.exit_code == 1
    assert "Invalid --mode" in result.stdout


def test_status_weak_empty(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    _promote_node(syca_home, "cmd", "健康节点", domain="test")

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--weak"])
    assert result.exit_code == 0
    assert "No weak nodes" in result.stdout


def test_status_weak_shows_failures(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "weak-cmd", "薄弱节点", domain="shell")
    for _ in range(3):
        record_recovery_outcome(
            node_id,
            rating=RecoverRating.FAIL,
            fail_type=FailType.PROCEDURE,
            home=syca_home,
        )

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--weak"])
    assert result.exit_code == 0
    assert "薄弱节点" in result.stdout
    assert "3" in result.stdout
    assert "procedure" in result.stdout
    assert "medium" in result.stdout


def test_status_weak_and_domain_mutually_exclusive(
    syca_home: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--weak", "--domain", "shell"])
    assert result.exit_code == 1
    assert "exactly one" in result.stdout


def test_status_no_args_shows_help(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))

    runner = CliRunner()
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Provide" in result.stdout
