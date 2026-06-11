from pathlib import Path

import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.utils.paths import CONFIG_FILENAME, DATABASE_FILENAME, SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    return home


def test_init_cli_creates_local_data_directory(syca_home: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Sycamore home:" in result.output
    assert syca_home.name in result.output
    assert (syca_home / CONFIG_FILENAME).exists()
    assert (syca_home / DATABASE_FILENAME).exists()


def test_init_cli_is_idempotent(syca_home: Path) -> None:
    runner = CliRunner()

    first = runner.invoke(app, ["init"])
    second = runner.invoke(app, ["init"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Already initialized" in second.output
