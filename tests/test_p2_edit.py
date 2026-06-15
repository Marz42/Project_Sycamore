"""Tests for Phase 2: completion, clarify, edit, check."""

from pathlib import Path

import frontmatter
import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.clarify_service import ClarifyError, suggest_promotion
from sycamore.core.completion import (
    CompletionState,
    _is_placeholder,
    assess_completion,
    is_draft,
)
from sycamore.core.edit_service import edit_node_block, get_edit_blocks
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.models.enums import CaptureKind
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import (
    extract_section,
    parse_node_markdown,
)
from sycamore.utils.paths import DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote(home: Path, content: str, title: str, domain: str = "test", node_type: str = "capability") -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(
        capture.id, title=title, domain=domain, node_type=node_type, home=home
    )
    return result.node.id


# ── Placeholder detection ────────────────────────────────────────────


def test_is_placeholder_detects_template_text() -> None:
    assert _is_placeholder("用自己的话解释这个能力")
    assert _is_placeholder("只放低频但实操必要的命令")
    assert _is_placeholder(None)
    assert _is_placeholder("")
    assert not _is_placeholder("This is user-written content about recursion.")


# ── Completion state ─────────────────────────────────────────────────


def test_draft_node_has_no_user_content(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "draft node")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;", (node_id,)
        ).fetchone()
        node_file = syca_home / row["node_path"]
    finally:
        connection.close()

    parsed = parse_node_markdown(node_file)
    report = assess_completion(parsed)
    assert report.state == CompletionState.DRAFT
    assert "Core Idea" in report.missing


def test_modeled_node_has_core_filled(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "modeled node")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;", (node_id,)
        ).fetchone()
        node_file = syca_home / row["node_path"]
    finally:
        connection.close()

    post = frontmatter.load(node_file)
    # Fill in Core Idea, Problem, Boundaries, Minimal Task
    post.content = post.content.replace(
        "用自己的话解释这个能力解决什么问题，以及背后的机制。",
        "Recursion solves problems by breaking them into smaller subproblems.",
    )
    post.content += "\n\n## Problem It Solves\n\nAvoids manual repetition.\n\n## Boundaries\n\n- May overflow stack\n\n## Minimal Task\n\nWrite a recursive factorial.\n\n## Contrast\n\nCompare with iteration.\n"
    node_file.write_text(frontmatter.dumps(post), encoding="utf-8")

    parsed = parse_node_markdown(node_file)
    report = assess_completion(parsed)
    assert report.state in (CompletionState.CONTRASTED, CompletionState.REVIEWABLE)


def test_reviewable_node_has_everything(syca_home: Path) -> None:
    node_id = _promote(syca_home, "grep", "full node")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;", (node_id,)
        ).fetchone()
        node_file = syca_home / row["node_path"]
    finally:
        connection.close()

    post = frontmatter.load(node_file)
    post.content = post.content.replace(
        "用自己的话解释这个能力解决什么问题，以及背后的机制。",
        "Grep filters lines matching a pattern.",
    )
    post.content = post.content.replace(
        "只放低频但实操必要的命令、参数和配置。",
        "grep -r pattern dir/",
    )
    post.content += "\n\n## Problem It Solves\n\nFind text in files.\n\n## Boundaries\n\n- Text only\n\n## Minimal Task\n\nFind lines with 'error'.\n\n## Contrast\n\nDifferent from sed.\n"
    node_file.write_text(frontmatter.dumps(post), encoding="utf-8")

    parsed = parse_node_markdown(node_file)
    report = assess_completion(parsed)
    assert report.state == CompletionState.REVIEWABLE
    assert len(report.missing) == 0


def test_is_draft_shortcut(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "draft")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;", (node_id,)
        ).fetchone()
        node_file = syca_home / row["node_path"]
    finally:
        connection.close()

    parsed = parse_node_markdown(node_file)
    assert is_draft(parsed) is True


# ── Edit blocks ──────────────────────────────────────────────────────


def test_get_edit_blocks_for_capability() -> None:
    blocks = get_edit_blocks("capability")
    names = [b[0] for b in blocks]
    assert "Core Idea" in names
    assert "Steps" in names
    assert "Cheatsheet" in names
    assert "Contrast" in names
    assert "Minimal Task" in names


def test_get_edit_blocks_for_concept() -> None:
    blocks = get_edit_blocks("concept")
    names = [b[0] for b in blocks]
    assert "Core Thesis" in names
    assert "Historical Context" in names
    assert "Critique" in names


def test_edit_node_block_writes_content(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "edit test")
    result = edit_node_block(node_id, "Core Idea", "Updated content.", home=syca_home)
    assert result.written is True
    assert result.block == "Core Idea"

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;", (node_id,)
        ).fetchone()
        node_file = syca_home / row["node_path"]
    finally:
        connection.close()

    parsed = parse_node_markdown(node_file)
    core = extract_section(parsed.body, "Core Idea")
    assert core is not None
    assert "Updated content" in core


def test_edit_node_block_creates_new_section(syca_home: Path) -> None:
    node_id = _promote(syca_home, "cmd", "contrast test")
    result = edit_node_block(node_id, "Contrast", "Contrast content.", home=syca_home)
    assert result.written is True

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT node_path FROM ability_nodes WHERE id = ?;", (node_id,)
        ).fetchone()
        node_file = syca_home / row["node_path"]
    finally:
        connection.close()

    parsed = parse_node_markdown(node_file)
    contrast = extract_section(parsed.body, "Contrast")
    assert contrast is not None
    assert "Contrast content" in contrast


# ── Clarify tests ────────────────────────────────────────────────────


def test_suggest_promotion_from_cheat(syca_home: Path) -> None:
    create_capture(kind=CaptureKind.CHEAT, content="docker ps -a", home=syca_home)
    suggestion = suggest_promotion(home=syca_home)

    assert suggestion.suggested_type in ("capability", "concept", "theorem", "process")
    assert suggestion.suggested_title
    assert suggestion.capture.content == "docker ps -a"


def test_suggest_promotion_from_note(syca_home: Path) -> None:
    create_capture(
        kind=CaptureKind.NOTE,
        content="理解了这个框架的核心主张，它能解释很多历史现象",
        home=syca_home,
    )
    suggestion = suggest_promotion(home=syca_home)

    # Should detect concept type from keywords
    assert suggestion.suggested_type == "concept"


def test_clarify_with_empty_inbox_raises(syca_home: Path) -> None:
    with pytest.raises(ClarifyError):
        suggest_promotion(home=syca_home)


# ── CLI tests ────────────────────────────────────────────────────────


def test_clarify_cli(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    create_capture(kind=CaptureKind.CHEAT, content="git log --oneline", home=syca_home)

    runner = CliRunner()
    result = runner.invoke(app, ["clarify"])
    assert result.exit_code == 0
    assert "Suggested type" in result.stdout
    assert "syca promote" in result.stdout


def test_check_cli_draft(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote(syca_home, "cmd", "draft node")

    runner = CliRunner()
    result = runner.invoke(app, ["check", node_id])
    assert result.exit_code == 0
    assert "draft" in result.stdout


def test_status_completion(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    _promote(syca_home, "cmd", "draft node")

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--completion", "draft"])
    assert result.exit_code == 0
    assert "draft" in result.stdout


def test_edit_cli_block_prompt(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote(syca_home, "cmd", "interactive edit")

    # Test with --block flag (non-interactive, verifies it runs)
    runner = CliRunner()
    # Without input, edit will fail on prompt. Just test it loads correctly.
    result = runner.invoke(app, ["edit", node_id, "--block", "nonexistent"])
    assert result.exit_code == 1
    assert "Unknown block" in result.stdout


def test_edit_cli_suggest_flag(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--suggest flag should load without error (mock provider will return suggestion)."""
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote(syca_home, "cmd", "suggest test")

    runner = CliRunner()
    # Non-interactive test: use --block with --suggest, input empty to skip
    result = runner.invoke(
        app,
        ["edit", node_id, "--block", "Core Idea", "--suggest"],
        input="\n",  # empty → skip
    )
    assert result.exit_code == 0
    # Mock suggestion text should appear
    assert "Suggestion:" in result.stdout


def test_mock_provider_suggest_fill() -> None:
    from sycamore.review.provider import MockReviewProvider
    provider = MockReviewProvider()
    result = provider.suggest_fill("test prompt")
    assert "Mock suggestion" in result


def test_mock_provider_has_suggest_fill_attr() -> None:
    """Verify MockReviewProvider satisfies the suggest_fill protocol."""
    from sycamore.review.provider import MockReviewProvider
    provider = MockReviewProvider()
    assert hasattr(provider, "suggest_fill")
    assert callable(provider.suggest_fill)
