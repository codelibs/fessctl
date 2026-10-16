import json

import pytest
from typer.testing import CliRunner

from fessctl.commands.systeminfo import systeminfo_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_systeminfo_json(runner, fess_service):
    result = runner.invoke(systeminfo_app, ["--output", "json"])
    assert result.exit_code == 0, f"Systeminfo failed: {result.stdout}"
    response = json.loads(result.stdout).get("response", {})
    assert response.get("status") == 0
    for key in ("bug_report_props", "env_props", "fess_props", "system_props"):
        props = response.get(key)
        assert isinstance(props, list) and props, f"{key} is empty"
        assert all("label" in p and "value" in p for p in props)
    assert "java.runtime.version" in [p["label"] for p in response["bug_report_props"]]


def test_systeminfo_text(runner, fess_service):
    result = runner.invoke(systeminfo_app, [])
    assert result.exit_code == 0, f"Systeminfo failed: {result.stdout}"
    for title in ("## Bug Report", "## Environment", "## Fess", "## System"):
        assert title in result.stdout
    assert "| java.runtime.version |" in result.stdout
