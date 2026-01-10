import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.joblog import joblog_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_joblog_list(runner, fess_service):
    """
    Test listing job log entries.
    JobLogs are populated by scheduler runs, so we just verify
    that the list command executes successfully.
    """
    result = runner.invoke(
        joblog_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    # logs may be empty if no jobs have run
    logs = list_resp["response"].get("logs", [])
    assert isinstance(logs, list)


def test_joblog_list_with_pagination(runner, fess_service):
    """
    Test listing job log entries with pagination options.
    """
    result = runner.invoke(
        joblog_app,
        ["list", "--page", "1", "--size", "10", "--output", "json"]
    )
    assert result.exit_code == 0, f"List with pagination failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0


def test_joblog_list_yaml_output(runner, fess_service):
    """
    Test listing job log entries with YAML output format.
    """
    result = runner.invoke(
        joblog_app,
        ["list", "--output", "yaml"]
    )
    assert result.exit_code == 0, f"List YAML failed: {result.stdout}"
    # YAML output should contain 'response:' key
    assert "response:" in result.stdout or "logs:" in result.stdout


def test_joblog_list_text_output(runner, fess_service):
    """
    Test listing job log entries with text output format.
    """
    result = runner.invoke(
        joblog_app,
        ["list", "--output", "text"]
    )
    # Should succeed even with text output
    assert result.exit_code == 0, f"List text failed: {result.stdout}"


def test_joblog_get_nonexistent(runner, fess_service):
    """
    Test getting a non-existent job log entry returns an error.
    """
    result = runner.invoke(
        joblog_app,
        ["get", "nonexistent-id-12345"]
    )
    assert result.exit_code != 0
    assert "failed to retrieve joblog" in result.stdout.lower()


def test_joblog_get_nonexistent_json_output(runner, fess_service):
    """
    Test getting a non-existent job log entry with JSON output.
    """
    result = runner.invoke(
        joblog_app,
        ["get", "nonexistent-id-12345", "--output", "json"]
    )
    # JSON output always returns, but status should indicate failure
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") != 0


def test_joblog_delete_nonexistent(runner, fess_service):
    """
    Test deleting a non-existent job log entry returns an error.
    """
    result = runner.invoke(
        joblog_app,
        ["delete", "nonexistent-id-12345"]
    )
    assert result.exit_code != 0
    assert "failed to delete joblog" in result.stdout.lower()


def test_joblog_delete_nonexistent_json_output(runner, fess_service):
    """
    Test deleting a non-existent job log entry with JSON output.
    """
    result = runner.invoke(
        joblog_app,
        ["delete", "nonexistent-id-12345", "--output", "json"]
    )
    # JSON output always returns, but status should indicate failure
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") != 0
