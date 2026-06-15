"""Tests for NodeType infrastructure — templates, sync, doctor, CLI."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.doctor_service import run_doctor
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.core.sync_service import sync_nodes
from sycamore.models.enums import CaptureKind
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import parse_node_markdown
from sycamore.storage.markdown_store import (
    _seed_body_capability,
    _seed_body_concept,
    _seed_body_process,
    _seed_body_theorem,
)
from sycamore.storage.node_repository import get_node_by_id
from sycamore.utils.paths import DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


# ── Template tests ──────────────────────────────────────────────────


def test_capability_template_has_expected_sections() -> None:
    body = _seed_body_capability("Test", "content", "", "ls -la")
    assert "## Mental Model" in body
    assert "### Core Idea" in body
    assert "### Boundaries" in body
    assert "## Steps" in body
    assert "## Pitfalls" in body
    assert "## Cheatsheet" in body
    assert "ls -la" in body


def test_concept_template_has_expected_sections() -> None:
    body = _seed_body_concept("Test", "核心主张", "")
    assert "## Core Thesis" in body
    assert "## Historical Context" in body
    assert "## Critique" in body
    assert "## Apply To" in body
    assert "## Cheatsheet" not in body


def test_theorem_template_has_expected_sections() -> None:
    body = _seed_body_theorem("Test", "E=mc^2", "")
    assert "## Formula" in body
    assert "## Intuition" in body
    assert "## Boundary Conditions" in body
    assert "## Counterexamples" in body
    assert "E=mc^2" in body


def test_process_template_has_expected_sections() -> None:
    body = _seed_body_process("Test", "机理描述", "")
    assert "## Mechanism" in body
    assert "## Parameters" in body
    assert "## Disturbance Response" in body


# ── Front matter type tests ──────────────────────────────────────────


def test_promote_writes_type_in_front_matter(syca_home: Path) -> None:
    cap = create_capture(kind=CaptureKind.NOTE, content="test concept")
    result = promote_capture(cap.id, node_type="concept")

    parsed = parse_node_markdown(result.node_file)
    assert parsed.node_type == "concept"


def test_promote_default_type_is_capability(syca_home: Path) -> None:
    cap = create_capture(kind=CaptureKind.CHEAT, content="ls -la")
    result = promote_capture(cap.id)

    parsed = parse_node_markdown(result.node_file)
    assert parsed.node_type == "capability"


def test_promote_indexes_node_type(syca_home: Path) -> None:
    cap = create_capture(kind=CaptureKind.NOTE, content="theorem test")
    result = promote_capture(cap.id, node_type="theorem")

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        node = get_node_by_id(connection, result.node.id)
        assert node is not None
        assert node.node_type == "theorem"
    finally:
        connection.close()


# ── Sync tests ───────────────────────────────────────────────────────


def test_sync_preserves_node_type(syca_home: Path) -> None:
    cap = create_capture(kind=CaptureKind.NOTE, content="sync test")
    result = promote_capture(cap.id, node_type="process")

    sync_nodes(home=syca_home)

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        node = get_node_by_id(connection, result.node.id)
        assert node is not None
        assert node.node_type == "process"
    finally:
        connection.close()


def test_sync_defaults_missing_type_to_capability(syca_home: Path) -> None:
    cap = create_capture(kind=CaptureKind.NOTE, content="no type")
    result = promote_capture(cap.id)  # defaults to capability

    # Manually strip type from front matter
    text = result.node_file.read_text(encoding="utf-8")
    # Remove the type line
    lines = text.splitlines()
    filtered = [line for line in lines if not line.startswith("type:")]
    result.node_file.write_text("\n".join(filtered), encoding="utf-8")

    sync_nodes(home=syca_home)

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        node = get_node_by_id(connection, result.node.id)
        assert node is not None
        assert node.node_type == "capability"
    finally:
        connection.close()


# ── Doctor tests ─────────────────────────────────────────────────────


def test_sync_defaults_invalid_type_to_capability(syca_home: Path) -> None:
    """Sync should safely default an invalid front matter type to capability."""
    cap = create_capture(kind=CaptureKind.NOTE, content="bad type test")
    result = promote_capture(cap.id)

    text = result.node_file.read_text(encoding="utf-8")
    text = text.replace("type: capability", "type: invalid_type")
    result.node_file.write_text(text, encoding="utf-8")

    # Sync should not crash — it defaults to capability
    sync_result = sync_nodes(home=syca_home)
    assert sync_result.synced == 1

    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        node = get_node_by_id(connection, result.node.id)
        assert node is not None
        assert node.node_type == "capability"
    finally:
        connection.close()


def test_doctor_accepts_all_valid_types(syca_home: Path) -> None:
    for node_type in ("capability", "concept", "theorem", "process"):
        cap = create_capture(kind=CaptureKind.NOTE, content=f"{node_type} node")
        result = promote_capture(cap.id, node_type=node_type)
        sync_nodes(home=syca_home)

        report = run_doctor(home=syca_home)
        issues_about_this_node = [
            i for i in report.issues
            if i.path and result.node.node_path in i.path
        ]
        assert not any(
            i.code == "invalid_node_type" for i in issues_about_this_node
        ), f"Doctor flagged valid type '{node_type}'"


# ── CLI tests ────────────────────────────────────────────────────────


def test_promote_cli_default_type_is_capability(syca_home: Path) -> None:
    runner = CliRunner()
    runner.invoke(app, ["capture", "--note", "cli test"])

    result = runner.invoke(app, ["promote", "--index", "1"])
    assert result.exit_code == 0

    # Verify the generated markdown has type: capability
    nodes_dir = syca_home / "nodes"
    md_files = list(nodes_dir.glob("*.md"))
    assert len(md_files) == 1
    parsed = parse_node_markdown(md_files[0])
    assert parsed.node_type == "capability"


def test_promote_cli_explicit_type(syca_home: Path) -> None:
    runner = CliRunner()
    runner.invoke(app, ["capture", "--note", "concept test"])

    result = runner.invoke(app, ["promote", "--index", "1", "--type", "concept"])
    assert result.exit_code == 0

    nodes_dir = syca_home / "nodes"
    md_files = list(nodes_dir.glob("*.md"))
    assert len(md_files) == 1
    parsed = parse_node_markdown(md_files[0])
    assert parsed.node_type == "concept"
    assert "## Core Thesis" in parsed.body


# ── Schema migration test ────────────────────────────────────────────


def test_schema_migration_adds_node_type_column(syca_home: Path) -> None:
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute("PRAGMA table_info(ability_nodes);").fetchall()
        columns = {r["name"] for r in row}
        assert "node_type" in columns
    finally:
        connection.close()
