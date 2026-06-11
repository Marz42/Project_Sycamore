from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore import __version__
from sycamore.cli.app import app
from sycamore.utils.paths import SYCA_HOME_ENV


runner = CliRunner()


def test_help_shows_capture_first_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "capture" in result.output
    assert "inbox" in result.output
    assert "promote" in result.output
    assert "doctor" in result.output


def test_version_option() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert f"syca {__version__}" in result.output


def test_capture_requires_exactly_one_kind() -> None:
    result = runner.invoke(app, ["capture"])

    assert result.exit_code == 1
    assert "Choose exactly one" in result.output


def test_capture_without_init_reports_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "missing-init"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    result = runner.invoke(app, ["capture", "--note", "awk field separators caused trouble"])

    assert result.exit_code == 1
    assert "Run `syca init` first" in result.output
