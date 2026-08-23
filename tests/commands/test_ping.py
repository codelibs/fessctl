import json
import pytest
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClient
from fessctl.cli import app
from fessctl.config.settings import Settings


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_ping_reports_a_healthy_server(runner, fess_service):
    """
    A server the test harness already waited for must be reported as healthy,
    whatever spelling of the cluster status the running Fess version uses.
    """
    result = runner.invoke(app, ["ping"])
    assert result.exit_code == 0, f"Ping failed: {result.stdout}"
    assert "error" not in result.stdout.lower(), result.stdout


def test_ping_json_reports_a_usable_cluster(runner, fess_service):
    """
    The raw health payload must carry a green or yellow cluster status.
    """
    result = runner.invoke(app, ["ping", "--output", "json"])
    assert result.exit_code == 0, f"Ping failed: {result.stdout}"
    payload = json.loads(result.stdout)

    if FessAPIClient(Settings()).is_api_v2:
        status = payload["response"]["engine"]["status"]
    else:
        status = payload["data"]["status"]

    assert status.lower() in ("green", "yellow"), f"Unexpected cluster status: {status}"
