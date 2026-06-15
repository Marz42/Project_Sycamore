"""Tests for Phase 4: path view, cluster risk, new edge types."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.link_service import create_link
from sycamore.core.path_service import PathError, build_path_report
from sycamore.core.promote_service import promote_capture
from sycamore.core.recover_service import RecoverRating, record_recovery_outcome
from sycamore.core.status_service import list_cluster_risk
from sycamore.core.transfer_service import TransferLevel, TransferOutcome, record_transfer_outcome
from sycamore.models.enums import CaptureKind, EdgeType
from sycamore.utils.paths import SYCA_HOME_ENV


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


# ── New edge types ───────────────────────────────────────────────────


def test_create_contrast_edge(syca_home: Path) -> None:
    a = _promote(syca_home, "a", "节点A", domain="dev")
    b = _promote(syca_home, "b", "节点B", domain="dev")

    result = create_link(a, b, edge_type=EdgeType.CONTRAST, home=syca_home)
    assert result.edge.edge_type == EdgeType.CONTRAST


def test_create_composition_edge(syca_home: Path) -> None:
    a = _promote(syca_home, "a", "节点A", domain="dev")
    b = _promote(syca_home, "b", "节点B", domain="dev")

    result = create_link(a, b, edge_type=EdgeType.COMPOSITION, home=syca_home)
    assert result.edge.edge_type == EdgeType.COMPOSITION


def test_create_diagnostic_edge(syca_home: Path) -> None:
    a = _promote(syca_home, "a", "问题节点", domain="dev")
    b = _promote(syca_home, "b", "方案节点", domain="dev")

    result = create_link(a, b, edge_type=EdgeType.DIAGNOSTIC, home=syca_home)
    assert result.edge.edge_type == EdgeType.DIAGNOSTIC


def test_old_contrasts_with_still_works(syca_home: Path) -> None:
    a = _promote(syca_home, "a", "节点A", domain="dev")
    b = _promote(syca_home, "b", "节点B", domain="dev")

    result = create_link(a, b, edge_type=EdgeType.CONTRASTS_WITH, home=syca_home)
    assert result.edge.edge_type == EdgeType.CONTRASTS_WITH


# ── Path view ────────────────────────────────────────────────────────


def test_path_view_empty_domain_raises(syca_home: Path) -> None:
    with pytest.raises(PathError, match="No nodes"):
        build_path_report("nonexistent", home=syca_home)


def test_path_view_single_node(syca_home: Path) -> None:
    _promote(syca_home, "cd", "切换目录", domain="shell")

    report = build_path_report("shell", home=syca_home)
    assert report.domain == "shell"
    assert len(report.unlinked) == 1


def test_path_view_prerequisite_chain(syca_home: Path) -> None:
    a = _promote(syca_home, "cd", "切换目录", domain="shell")
    b = _promote(syca_home, "pwd", "查看目录", domain="shell")
    c = _promote(syca_home, "ls", "列出文件", domain="shell")

    create_link(a, b, edge_type=EdgeType.PREREQUISITE, home=syca_home)
    create_link(b, c, edge_type=EdgeType.PREREQUISITE, home=syca_home)

    report = build_path_report("shell", home=syca_home)
    assert len(report.chains) >= 1
    # Should find at least one chain
    chain = report.chains[0]
    assert len(chain.nodes) >= 2


def test_path_view_with_composition(syca_home: Path) -> None:
    a = _promote(syca_home, "grep", "grep过滤", domain="shell")
    b = _promote(syca_home, "awk", "awk处理", domain="shell")

    create_link(a, b, edge_type=EdgeType.COMPOSITION, home=syca_home)

    report = build_path_report("shell", home=syca_home)
    assert len(report.chains) >= 1


# ── Cluster risk ─────────────────────────────────────────────────────


def test_cluster_risk_empty(syca_home: Path) -> None:
    _promote(syca_home, "cmd", "健康节点", domain="shell")

    report = list_cluster_risk(home=syca_home)
    # No fails → empty
    assert len(report.entries) == 0


def test_cluster_risk_detects_domain_with_fails(syca_home: Path) -> None:
    a = _promote(syca_home, "hard", "困难节点", domain="shell")
    b = _promote(syca_home, "mid", "中等节点", domain="shell")

    record_recovery_outcome(a, rating=RecoverRating.FAIL, home=syca_home)
    record_recovery_outcome(a, rating=RecoverRating.FAIL, home=syca_home)
    record_recovery_outcome(b, rating=RecoverRating.FAIL, home=syca_home)

    report = list_cluster_risk(home=syca_home)
    assert len(report.entries) == 1
    entry = report.entries[0]
    assert entry.domain == "shell"
    assert entry.recover_fails == 3
    assert entry.node_count == 2
    # 3 fails / 2 nodes = 1.5 → medium risk
    assert entry.risk_level == "medium"


def test_cluster_risk_multi_domain(syca_home: Path) -> None:
    a = _promote(syca_home, "a", "节点A", domain="shell")
    b = _promote(syca_home, "b", "节点B", domain="dev")

    record_recovery_outcome(a, rating=RecoverRating.FAIL, home=syca_home)
    record_transfer_outcome(b, level=TransferLevel.A, outcome=TransferOutcome.FAIL, home=syca_home)

    report = list_cluster_risk(home=syca_home)
    assert len(report.entries) >= 1


# ── CLI tests ────────────────────────────────────────────────────────


def test_path_cli(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    a = _promote(syca_home, "cd", "切换目录", domain="shell")
    b = _promote(syca_home, "pwd", "查看目录", domain="shell")
    create_link(a, b, edge_type=EdgeType.PREREQUISITE, home=syca_home)

    runner = CliRunner()
    result = runner.invoke(app, ["path", "--domain", "shell"])
    assert result.exit_code == 0
    assert "切换目录" in result.stdout


def test_path_cli_empty_domain(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))

    runner = CliRunner()
    result = runner.invoke(app, ["path", "--domain", "nonexistent"])
    assert result.exit_code == 1


def test_status_cluster_risk_cli(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    a = _promote(syca_home, "hard", "困难节点", domain="shell")
    record_recovery_outcome(a, rating=RecoverRating.FAIL, home=syca_home)

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--cluster-risk"])
    assert result.exit_code == 0
    assert "shell" in result.stdout


def test_status_cluster_risk_empty(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    _promote(syca_home, "cmd", "健康节点", domain="shell")

    runner = CliRunner()
    result = runner.invoke(app, ["status", "--cluster-risk"])
    assert result.exit_code == 0
    assert "No failure clusters" in result.stdout


def test_link_cli_new_edge_types(syca_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYCA_HOME_ENV, str(syca_home))
    a = _promote(syca_home, "a", "节点A", domain="dev")
    b = _promote(syca_home, "b", "节点B", domain="dev")

    runner = CliRunner()
    for etype in ("contrast", "composition", "diagnostic"):
        result = runner.invoke(app, ["link", a, b, "--type", etype])
        assert result.exit_code == 0, f"Failed for {etype}"
        assert "Linked" in result.stdout
