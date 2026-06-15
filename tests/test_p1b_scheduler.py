"""Tests for Phase 1B: FSRS-5 scheduler."""

import math
from pathlib import Path

import pytest

from sycamore.core.capture_service import create_capture
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.core.recover_service import (
    RecoverRating,
    record_recovery_outcome,
)
from sycamore.core.scheduler import (
    _R,
    _S0,
    _D0,
    _next_D,
    _next_S,
    _next_interval,
    current_retrievability,
    init_state,
    rating_to_int,
    update_state,
)
from sycamore.models.enums import CaptureKind
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote(home: Path, content: str, title: str, domain: str = "test") -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(capture.id, title=title, domain=domain, home=home)
    return result.node.id


# ── Rating mapping ───────────────────────────────────────────────────


def test_rating_to_int() -> None:
    assert rating_to_int("fail") == 1
    assert rating_to_int("hard") == 2
    assert rating_to_int("pass") == 3
    assert rating_to_int("easy") == 4


# ── Core FSRS formulas ───────────────────────────────────────────────


def test_R_monotonic() -> None:
    """Retrievability decreases with time."""
    r1 = _R(1, 30)
    r10 = _R(10, 30)
    r30 = _R(30, 30)
    assert r1 > r10 > r30


def test_R_at_zero_is_one() -> None:
    assert math.isclose(_R(0, 30), 1.0)


def test_S0_increases_with_rating() -> None:
    assert _S0(1) < _S0(2) < _S0(3) < _S0(4)


def test_D0_decreases_with_rating() -> None:
    """Higher initial ratings produce lower difficulty."""
    assert _D0(1) > _D0(4)


def test_next_D_stays_in_range() -> None:
    for G in (1, 2, 3, 4):
        for D in (1.0, 3.0, 5.0, 7.0, 10.0):
            D_new = _next_D(G, D)
            assert 1.0 <= D_new <= 10.0


def test_next_S_grows_for_pass() -> None:
    S_new = _next_S(3, 5.0, 10.0, 0.9)  # pass
    assert S_new > 10.0  # stability increases


def test_next_S_hard_penalty() -> None:
    S_hard = _next_S(2, 5.0, 10.0, 0.9)  # hard
    S_good = _next_S(3, 5.0, 10.0, 0.9)  # good
    assert S_hard < S_good


def test_next_S_easy_bonus() -> None:
    S_easy = _next_S(4, 5.0, 10.0, 0.9)
    S_good = _next_S(3, 5.0, 10.0, 0.9)
    assert S_easy > S_good


def test_next_interval_increases_with_stability() -> None:
    i1 = _next_interval(30, 0.9)
    i2 = _next_interval(100, 0.9)
    assert i2 > i1


def test_next_interval_shorter_for_lower_retention() -> None:
    # Higher retention → shorter interval (review more often to maintain higher R)
    i_low = _next_interval(100, 0.8)
    i_high = _next_interval(100, 0.95)
    assert i_low > i_high


# ── State lifecycle ──────────────────────────────────────────────────


def test_init_state_creates_due_at() -> None:
    state = init_state("pass", now_iso="2026-01-01T00:00:00+00:00")
    assert state.stability > 0
    assert state.difficulty > 0
    assert state.due_at is not None
    assert state.due_at > "2026-01-01T00:00:00+00:00"
    assert state.review_count == 1


def test_update_state_grows_interval_on_consecutive_pass() -> None:
    state = init_state("pass", now_iso="2026-01-01T00:00:00+00:00")
    s1 = state.stability
    state = update_state(state, "pass", now_iso="2026-02-01T00:00:00+00:00")
    assert state.stability >= s1  # stability non-decreasing on pass
    assert state.review_count == 2


def test_three_pass_then_interval_grows() -> None:
    state = init_state("pass", now_iso="2026-01-01T00:00:00+00:00")
    s0 = state.stability
    state = update_state(state, "pass", now_iso="2026-01-15T00:00:00+00:00")
    state = update_state(state, "pass", now_iso="2026-02-01T00:00:00+00:00")
    state = update_state(state, "pass", now_iso="2026-03-01T00:00:00+00:00")
    assert state.stability > s0 * 2  # significantly larger


def test_current_retrievability() -> None:
    state = init_state("hard", now_iso="2026-01-01T00:00:00+00:00")
    r_now = current_retrievability(state, "2026-01-02T00:00:00+00:00")
    assert 0 < r_now < 1


# ── Integration: recover updates scheduler state ─────────────────────


def test_recover_initializes_scheduler_state(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "测试节点")
    record_recovery_outcome(node_id, rating=RecoverRating.PASS, home=syca_home)

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT * FROM node_scheduler_state WHERE node_id = ?;",
            (node_id,),
        ).fetchone()
        assert row is not None
        assert row["stability"] > 0
        assert row["review_count"] == 1
        assert row["due_at"] is not None
    finally:
        connection.close()


def test_recover_updates_scheduler_state(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "渐变节点")
    record_recovery_outcome(node_id, rating=RecoverRating.PASS, home=syca_home)

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT stability FROM node_scheduler_state WHERE node_id = ?;",
            (node_id,),
        ).fetchone()
        s1 = row["stability"]
    finally:
        connection.close()

    # Second review — verify review_count increments
    record_recovery_outcome(node_id, rating=RecoverRating.PASS, home=syca_home)

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT stability, review_count FROM node_scheduler_state WHERE node_id = ?;",
            (node_id,),
        ).fetchone()
        assert row["stability"] >= s1  # stability should not decrease on pass
        assert row["review_count"] == 2
    finally:
        connection.close()


def test_recover_fail_increments_lapse_count(syca_home: Path) -> None:
    node_id = _promote(syca_home, "hard-cmd", "易忘节点")
    record_recovery_outcome(node_id, rating=RecoverRating.PASS, home=syca_home)
    record_recovery_outcome(
        node_id, rating=RecoverRating.FAIL, home=syca_home
    )

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT lapse_count FROM node_scheduler_state WHERE node_id = ?;",
            (node_id,),
        ).fetchone()
        assert row["lapse_count"] == 1
    finally:
        connection.close()


def test_recover_multiple_nodes_each_have_state(syca_home: Path) -> None:
    a = _promote(syca_home, "a", "节点A")
    b = _promote(syca_home, "b", "节点B")

    record_recovery_outcome(a, rating=RecoverRating.EASY, home=syca_home)
    record_recovery_outcome(b, rating=RecoverRating.HARD, home=syca_home)

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM node_scheduler_state;"
        ).fetchone()[0]
        assert count == 2
    finally:
        connection.close()


# ── CLI tests ────────────────────────────────────────────────────────


def test_schedule_cli_empty(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    from typer.testing import CliRunner
    from sycamore.cli.app import app

    runner = CliRunner()
    result = runner.invoke(app, ["schedule"])
    assert result.exit_code == 0
    assert "No nodes with scheduler state" in result.stdout


def test_schedule_cli_shows_due(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    from typer.testing import CliRunner
    from sycamore.cli.app import app

    node_id = _promote(syca_home, "cmd", "到期节点")
    record_recovery_outcome(node_id, rating=RecoverRating.PASS, home=syca_home)

    runner = CliRunner()
    result = runner.invoke(app, ["schedule", "--limit", "5"])
    assert result.exit_code == 0
    assert "到期节点" in result.stdout


def test_schedule_cli_domain_filter(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    from typer.testing import CliRunner
    from sycamore.cli.app import app

    a = _promote(syca_home, "cmd", "Shell节点", domain="shell")
    b = _promote(syca_home, "cmd", "Dev节点", domain="dev")
    record_recovery_outcome(a, rating=RecoverRating.PASS, home=syca_home)
    record_recovery_outcome(b, rating=RecoverRating.PASS, home=syca_home)

    runner = CliRunner()
    result = runner.invoke(app, ["schedule", "--domain", "shell"])
    assert result.exit_code == 0
    assert "Shell节点" in result.stdout
    assert "Dev节点" not in result.stdout


# ── Schema migration test ────────────────────────────────────────────


def test_scheduler_state_table_exists(syca_home: Path) -> None:
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute("PRAGMA table_info(node_scheduler_state);").fetchall()
        columns = {r["name"] for r in row}
        for col in ("stability", "difficulty", "due_at", "last_review_at", "review_count", "lapse_count"):
            assert col in columns
    finally:
        connection.close()
