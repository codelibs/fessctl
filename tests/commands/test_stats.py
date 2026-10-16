import json

import pytest
from typer.testing import CliRunner

from fessctl.commands.stats import stats_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_stats_json(runner, fess_service):
    result = runner.invoke(stats_app, ["--output", "json"])
    assert result.exit_code == 0, f"Stats failed: {result.stdout}"
    response = json.loads(result.stdout).get("response", {})
    assert response.get("status") == 0
    stats = response.get("stats", {})
    for key in ("jvm", "os", "process", "engine", "fs"):
        assert key in stats, f"{key} is missing"
    assert stats["jvm"]["memory"]["heap"]["max"] > 0
    assert stats["engine"]["status"] in ("green", "yellow")


def test_stats_text(runner, fess_service):
    result = runner.invoke(stats_app, [])
    assert result.exit_code == 0, f"Stats failed: {result.stdout}"
    assert "| jvm.memory.heap.used |" in result.stdout
    assert "| engine.cluster_name |" in result.stdout
