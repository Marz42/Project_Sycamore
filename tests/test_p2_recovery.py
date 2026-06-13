from pathlib import Path

import frontmatter
import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.graph_service import GraphError, build_domain_graph
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.link_service import LinkError, create_link
from sycamore.core.promote_service import promote_capture
from sycamore.core.recover_service import preview_recovery_drill, record_recovery_outcome
from sycamore.core.status_service import list_domain_status
from sycamore.models.enums import CapabilityEventType, CaptureKind, EdgeType
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
) -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(capture.id, title=title, domain=domain, home=home)
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


def test_preview_recovery_drill_shows_sections(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "rg pattern", "我能用 ripgrep", domain="shell")
    _write_mental_model(syca_home, node_id, "ripgrep 比 grep 更快，适合代码搜索。")

    drill = preview_recovery_drill(node_id, home=syca_home)

    assert "ripgrep" in drill.mental_model
    assert "rg pattern" in (drill.cheatsheet or "")


def test_record_recovery_pass_creates_event(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "ls -la", "我能列出目录")

    result = record_recovery_outcome(node_id, passed=True, note="explained well", home=syca_home)

    assert result.passed is True
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        row = connection.execute(
            "SELECT type FROM capability_events WHERE node_id = ? AND type = ?;",
            (node_id, CapabilityEventType.RECOVERY_PASSED.value),
        ).fetchone()
        assert row is not None
    finally:
        connection.close()


def test_create_link_and_graph(syca_home: Path) -> None:
    source_id = _promote_node(syca_home, "cd", "我能切换目录", domain="shell")
    target_id = _promote_node(syca_home, "pwd", "我能查看当前目录", domain="shell")

    link_result = create_link(
        source_id,
        target_id,
        edge_type=EdgeType.PREREQUISITE,
        rationale="Need cwd before listing",
        home=syca_home,
    )
    assert link_result.edge.edge_type is EdgeType.PREREQUISITE

    graph = build_domain_graph("shell", home=syca_home)
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1

    with pytest.raises(LinkError, match="already exists"):
        create_link(source_id, target_id, home=syca_home)


def test_list_domain_status(syca_home: Path) -> None:
    node_id = _promote_node(syca_home, "grep foo", "我能 grep", domain="shell")
    connection = open_initialized_database(syca_home / DATABASE_FILENAME)
    try:
        connection.execute(
            "UPDATE ability_nodes SET created_at = ? WHERE id = ?;",
            ("2020-01-01T00:00:00+00:00", node_id),
        )
        connection.commit()
    finally:
        connection.close()

    report = list_domain_status("shell", home=syca_home, stale_after_days=30)
    assert len(report.entries) == 1
    assert report.entries[0].freshness.is_stale is True


def test_graph_unknown_domain_raises(syca_home: Path) -> None:
    with pytest.raises(GraphError, match="No nodes"):
        build_domain_graph("missing", home=syca_home)


def test_recover_cli_pass(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    node_id = _promote_node(syca_home, "echo hi", "我能 echo", domain="shell")

    runner = CliRunner()
    result = runner.invoke(app, ["recover", node_id, "--pass"])
    assert result.exit_code == 0
    assert "Recovery passed" in result.stdout


def test_link_cli(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    source_id = _promote_node(syca_home, "a", "节点 A", domain="dev")
    target_id = _promote_node(syca_home, "b", "节点 B", domain="dev")

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["link", source_id, target_id, "--type", "related", "--rationale", "same topic"],
    )
    assert result.exit_code == 0
    assert "Linked" in result.stdout


def test_graph_cli_renders_tree(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    source_id = _promote_node(syca_home, "cd", "切换目录", domain="shell")
    target_id = _promote_node(syca_home, "pwd", "查看目录", domain="shell")
    create_link(source_id, target_id, home=syca_home)

    runner = CliRunner()
    result = runner.invoke(app, ["graph", "--domain", "shell"])
    assert result.exit_code == 0
    assert "Domain: shell" in result.stdout
    assert "[prerequisite]" in result.stdout
