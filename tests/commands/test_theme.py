import json
import os

import pytest
from typer.testing import CliRunner

from fessctl.commands.theme import theme_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


@pytest.fixture(scope="module")
def theme_api(fess_service):
    """
    Skips when the Fess under test has no /api/admin/theme (added in Fess 15.9.0).
    """
    major, minor, *_ = (int(p) for p in os.getenv("FESS_VERSION", "15.9.0").split(".")[:2])
    if (major, minor) < (15, 9):
        pytest.skip("Fess under test does not provide /api/admin/theme")


def test_theme_available(runner, theme_api):
    result = runner.invoke(theme_app, ["available", "--output", "json"])
    assert result.exit_code == 0, f"Available failed: {result.stdout}"
    resp = json.loads(result.stdout)
    assert resp.get("response", {}).get("status") == 0
    themes = resp["response"].get("themes", [])
    assert isinstance(themes, list)
    assert all("name" in t and "version" in t for t in themes)


def test_theme_install_unknown_theme(runner, theme_api):
    result = runner.invoke(theme_app, ["install", "no-such-theme", "0.0.1"])
    assert result.exit_code != 0
    assert "failed to install theme" in result.stdout.lower()
