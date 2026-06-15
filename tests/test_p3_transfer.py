"""Tests for Phase 3: transfer service and CLI."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.core.transfer_service import (
    TransferLevel,
    TransferOutcome,
    _template_scenario,
    generate_scenario,
    get_transfer_count,
    record_transfer_outcome,
)
from sycamore.models.enums import CapabilityEventType, CaptureKind
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote(home: Path, content: str, title: str, domain: str = "shell") -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(capture.id, title=title, domain=domain, home=home)
    return result.node.id


# ── Template scenarios ───────────────────────────────────────────────


def test_template_scenario_generates_non_empty() -> None:
    from sycamore.models.ability_node import AbilityNode
    from sycamore.models.enums import ClaimedLevel, ReviewStatus

    node = AbilityNode(
        id="test", slug="test", title="我能 grep", domain="shell",
        node_type="capability", claimed_level=ClaimedLevel.L1,
        review_status=ReviewStatus.NOT_REVIEWED,
        node_path="nodes/test.md", content_hash="x", front_matter_hash="y",
        created_at="2026-01-01T00:00:00+00:00", updated_at="2026-01-01T00:00:00+00:00",
    )
    for level in TransferLevel:
        text = _template_scenario(node, level)
        assert len(text) > 20
        assert "grep" in text or "{" not in text  # no template markers


def test_generate_scenario_returns_template_fallback(syca_home: Path) -> None:
    """Without LLM configured, should fall back to template."""
    node_id = _promote(syca_home, "grep error", "我能 grep", domain="shell")
    scenario = generate_scenario(node_id, level=TransferLevel.A, home=syca_home)
    assert scenario.level == TransferLevel.A
    assert len(scenario.scenario) > 20


def test_generate_scenario_all_levels(syca_home: Path) -> None:
    node_id = _promote(syca_home, "ls", "我能列出目录", domain="shell")
    for level in TransferLevel:
        scenario = generate_scenario(node_id, level=level, home=syca_home)
        assert scenario.level == level
        assert scenario.description


# ── Outcome recording ────────────────────────────────────────────────


def test_record_transfer_success(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "测试节点")
    result = record_transfer_outcome(
        node_id,
        level=TransferLevel.A,
        outcome=TransferOutcome.SUCCESS,
        note="recognized instantly",
        home=syca_home,
    )
    assert result.outcome == TransferOutcome.SUCCESS
    assert result.level == TransferLevel.A

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT payload_json FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.TRANSFER_SUCCESS.value),
        ).fetchone()
        assert row is not None
        import json
        payload = json.loads(row["payload_json"])
        assert payload["level"] == "A"
        assert payload["outcome"] == "success"
        assert payload["note"] == "recognized instantly"
    finally:
        connection.close()


def test_record_transfer_fail(syca_home: Path) -> None:
    node_id = _promote(syca_home, "hard", "困难节点")
    result = record_transfer_outcome(
        node_id,
        level=TransferLevel.B,
        outcome=TransferOutcome.FAIL,
        home=syca_home,
    )
    assert result.outcome == TransferOutcome.FAIL


def test_record_transfer_partial(syca_home: Path) -> None:
    node_id = _promote(syca_home, "mid", "中等节点")
    result = record_transfer_outcome(
        node_id,
        level=TransferLevel.C,
        outcome=TransferOutcome.PARTIAL,
        home=syca_home,
    )
    assert result.outcome == TransferOutcome.PARTIAL


def test_get_transfer_count(syca_home: Path) -> None:
    node_id = _promote(syca_home, "count", "计数节点")
    record_transfer_outcome(node_id, level=TransferLevel.A, outcome=TransferOutcome.SUCCESS, home=syca_home)
    record_transfer_outcome(node_id, level=TransferLevel.B, outcome=TransferOutcome.PARTIAL, home=syca_home)
    record_transfer_outcome(node_id, level=TransferLevel.A, outcome=TransferOutcome.FAIL, home=syca_home)

    counts = get_transfer_count(node_id, home=syca_home)
    assert counts["success"] == 1
    assert counts["partial"] == 1
    assert counts["fail"] == 1


# ── CLI tests ────────────────────────────────────────────────────────


def test_transfer_cli_generates_scenario(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote(syca_home, "grep", "我能 grep", domain="shell")

    runner = CliRunner()
    result = runner.invoke(app, ["transfer", node_id, "--level", "A"])
    assert result.exit_code == 0
    assert "Scenario:" in result.stdout


def test_transfer_cli_records_outcome(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote(syca_home, "grep", "记录节点", domain="shell")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["transfer", node_id, "--level", "B", "--outcome", "success", "--note", "nailed it"],
    )
    assert result.exit_code == 0
    assert "success" in result.stdout


def test_transfer_cli_invalid_level(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote(syca_home, "cmd", "测试")

    runner = CliRunner()
    result = runner.invoke(app, ["transfer", node_id, "--level", "X"])
    assert result.exit_code == 1
    assert "Invalid level" in result.stdout


def test_transfer_cli_invalid_outcome(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote(syca_home, "cmd", "测试")

    runner = CliRunner()
    result = runner.invoke(app, ["transfer", node_id, "--level", "A", "--outcome", "unknown"])
    assert result.exit_code == 1
    assert "Invalid outcome" in result.stdout


def test_challenge_cli_random(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    _promote(syca_home, "grep", "grep节点", domain="shell")

    runner = CliRunner()
    result = runner.invoke(app, ["challenge"])
    assert result.exit_code == 0
    assert "Challenge:" in result.stdout
    assert "Scenario:" in result.stdout


def test_challenge_cli_domain(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    _promote(syca_home, "grep", "grep节点", domain="shell")

    runner = CliRunner()
    result = runner.invoke(app, ["challenge", "--domain", "shell"])
    assert result.exit_code == 0
    assert "Challenge:" in result.stdout
    assert "Scenario:" in result.stdout


def test_challenge_cli_empty_domain(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))

    runner = CliRunner()
    result = runner.invoke(app, ["challenge", "--domain", "nonexistent"])
    assert result.exit_code == 1
    assert "No nodes" in result.stdout
