import json

import pytest
from typer.testing import CliRunner

from fessctl.commands.failureurl import failureurl_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_failureurl_list(runner, fess_service):
    """
    FailureUrls are produced by crawls that hit errors, so we only verify that
    the list command (also with paging and filters) executes successfully.
    """
    result = runner.invoke(failureurl_app, ["list", "--output", "json"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    assert isinstance(list_resp["response"].get("logs", []), list)

    result = runner.invoke(
        failureurl_app,
        ["list", "--page", "1", "--size", "10", "--error-count-min", "1",
         "--error-name", "NoSuchError", "--url", "http://example.invalid/",
         "--output", "json"]
    )
    assert result.exit_code == 0, f"Filtered list failed: {result.stdout}"
    filtered = json.loads(result.stdout)
    assert filtered.get("response", {}).get("status") == 0
    assert filtered["response"].get("logs", []) == []


def test_failureurl_get_not_found(runner, fess_service):
    result = runner.invoke(failureurl_app, ["get", "--", "no-such-failureurl"])
    assert result.exit_code != 0
    assert "failed to retrieve failureurl" in result.stdout.lower()


def test_failureurl_delete_all(runner, fess_service):
    result = runner.invoke(failureurl_app, ["delete-all", "--yes", "--output", "json"])
    assert result.exit_code == 0, f"Delete all failed: {result.stdout}"
    assert json.loads(result.stdout).get("response", {}).get("status") == 0
