import json
import time

import pytest
from typer.testing import CliRunner

from fessctl.commands.plugin import plugin_app

# a small data store plugin, published for every Fess line
PLUGIN_NAME = "fess-ds-csv"


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def _plugins(runner, sub):
    result = runner.invoke(plugin_app, [sub, "--output", "json"])
    assert result.exit_code == 0, f"{sub} failed: {result.stdout}"
    resp = json.loads(result.stdout)
    assert resp.get("response", {}).get("status") == 0
    plugins = resp["response"].get("plugins", [])
    assert isinstance(plugins, list)
    return plugins


def _wait_until(runner, installed, name, timeout=60):
    """Install and uninstall are accepted at once and carried out in a background thread."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        present = any(p["name"] == name for p in _plugins(runner, "installed"))
        if present == installed:
            return True
        time.sleep(1)
    return False


def test_plugin_installed(runner, fess_service):
    plugins = _plugins(runner, "installed")
    assert all("name" in p and "version" in p for p in plugins)

    result = runner.invoke(plugin_app, ["installed"])
    assert result.exit_code == 0


def test_plugin_available(runner, fess_service):
    plugins = _plugins(runner, "available")
    assert all("name" in p and "version" in p for p in plugins)


def test_plugin_install_unknown_plugin(runner, fess_service):
    result = runner.invoke(plugin_app, ["install", "no-such-plugin", "0.0.1"])
    assert result.exit_code != 0
    assert "failed to install plugin" in result.stdout.lower()


def test_plugin_uninstall_aborts_without_confirmation(runner, fess_service):
    result = runner.invoke(plugin_app, ["uninstall", PLUGIN_NAME, "0.0.1"], input="n\n")
    assert result.exit_code != 0


def test_plugin_install_and_uninstall(runner, fess_service):
    if any(p["name"] == PLUGIN_NAME for p in _plugins(runner, "installed")):
        pytest.skip(f"{PLUGIN_NAME} is already installed in the Fess under test")
    candidates = [p for p in _plugins(runner, "available") if p["name"] == PLUGIN_NAME]
    if not candidates:
        pytest.skip(f"the Fess under test lists no {PLUGIN_NAME} (plugin repository unreachable?)")
    version = candidates[0]["version"]

    try:
        result = runner.invoke(plugin_app, ["install", PLUGIN_NAME, version])
        assert result.exit_code == 0, f"Install failed: {result.stdout}"
        assert _wait_until(runner, True, PLUGIN_NAME), f"{PLUGIN_NAME} was not installed in time"
    finally:
        result = runner.invoke(plugin_app, ["uninstall", PLUGIN_NAME, version, "--yes"])
        assert result.exit_code == 0, f"Uninstall failed: {result.stdout}"
        assert _wait_until(runner, False, PLUGIN_NAME), f"{PLUGIN_NAME} was not uninstalled in time"
