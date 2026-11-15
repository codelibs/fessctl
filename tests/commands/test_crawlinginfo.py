import json

import pytest
from typer.testing import CliRunner

from conftest import fess_version_at_least
from fessctl.commands.crawlinginfo import crawlinginfo_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_crawlinginfo_list(runner, fess_service):
    """
    Test listing crawling info entries.
    CrawlingInfo is typically populated by crawler runs, so we just verify
    that the list command executes successfully.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    # logs may be empty if no crawls have run
    logs = list_resp["response"].get("logs", [])
    assert isinstance(logs, list)


def test_crawlinginfo_list_with_pagination(runner, fess_service):
    """
    Test listing crawling info entries with pagination options.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["list", "--page", "1", "--size", "10", "--output", "json"]
    )
    assert result.exit_code == 0, f"List with pagination failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0


def test_crawlinginfo_list_yaml_output(runner, fess_service):
    """
    Test listing crawling info entries with YAML output format.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["list", "--output", "yaml"]
    )
    assert result.exit_code == 0, f"List YAML failed: {result.stdout}"
    # YAML output should contain 'response:' key
    assert "response:" in result.stdout or "logs:" in result.stdout


def test_crawlinginfo_list_text_output(runner, fess_service):
    """
    Test listing crawling info entries with text output format.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["list", "--output", "text"]
    )
    # Should succeed even with text output
    assert result.exit_code == 0, f"List text failed: {result.stdout}"


def test_crawlinginfo_get_nonexistent(runner, fess_service):
    """
    Test getting a non-existent crawling info entry returns an error.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["get", "nonexistent-id-12345"]
    )
    assert result.exit_code != 0
    assert "failed to retrieve crawlinginfo" in result.stdout.lower()


def test_crawlinginfo_get_nonexistent_json_output(runner, fess_service):
    """
    Test getting a non-existent crawling info entry with JSON output.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["get", "nonexistent-id-12345", "--output", "json"]
    )
    # JSON output always returns, but status should indicate failure
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") != 0


def test_crawlinginfo_delete_nonexistent(runner, fess_service):
    """
    Test deleting a non-existent crawling info entry returns an error.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["delete", "nonexistent-id-12345"]
    )
    assert result.exit_code != 0
    assert "failed to delete crawlinginfo" in result.stdout.lower()


def test_crawlinginfo_delete_nonexistent_json_output(runner, fess_service):
    """
    Test deleting a non-existent crawling info entry with JSON output.
    """
    result = runner.invoke(
        crawlinginfo_app,
        ["delete", "nonexistent-id-12345", "--output", "json"]
    )
    # JSON output always returns, but status should indicate failure
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") != 0


@pytest.fixture
def progress_api(fess_service):
    """
    Skips when the Fess under test has no /api/admin/crawlinginfo/progress (added in Fess 15.10).
    """
    if not fess_version_at_least(15, 10):
        pytest.skip("Fess under test does not provide /api/admin/crawlinginfo/progress")


def test_crawlinginfo_progress(runner, progress_api):
    """
    Whether a crawl is running is up to the Fess under test, so only the shape is checked.
    """
    result = runner.invoke(crawlinginfo_app, ["progress", "--output", "json"])
    assert result.exit_code == 0, f"Progress failed: {result.stdout}"
    resp = json.loads(result.stdout)["response"]
    assert resp["status"] == 0
    assert resp["total"] == len(resp["progress"])
    for entry in resp["progress"]:
        assert {"config_id", "name", "count", "last_count", "updated_time"} <= set(entry)

    result = runner.invoke(crawlinginfo_app, ["progress"])
    assert result.exit_code == 0, f"Progress failed: {result.stdout}"
    assert "No running crawls found." in result.stdout or "| NAME | CONFIG ID |" in result.stdout

    result = runner.invoke(crawlinginfo_app, ["progress", "--output", "yaml"])
    assert result.exit_code == 0
    assert "progress:" in result.stdout


def test_crawlinginfo_progress_rejects_a_bad_token(runner, progress_api, monkeypatch):
    monkeypatch.setenv("FESS_ACCESS_TOKEN", "no-such-token")
    result = runner.invoke(crawlinginfo_app, ["progress", "--output", "json"])
    assert result.exit_code != 0
    assert json.loads(result.stdout)["response"]["status"] != 0


def test_crawlinginfo_delete_all_aborts_without_confirmation(runner, fess_service):
    result = runner.invoke(crawlinginfo_app, ["delete-all"], input="n\n")
    assert result.exit_code != 0


def test_crawlinginfo_delete_all(runner, fess_service):
    """
    Deletes every session that is not running; the sessions go after the index refresh.
    """
    result = runner.invoke(crawlinginfo_app, ["delete-all", "--yes", "--output", "json"])
    assert result.exit_code == 0, f"Delete all failed: {result.stdout}"
    assert json.loads(result.stdout)["response"]["status"] == 0

    result = runner.invoke(crawlinginfo_app, ["delete-all", "--yes"])
    assert result.exit_code == 0
    assert "deleted successfully" in result.stdout


def test_crawlinginfo_delete_all_rejects_a_bad_token(runner, fess_service, monkeypatch):
    monkeypatch.setenv("FESS_ACCESS_TOKEN", "no-such-token")
    result = runner.invoke(crawlinginfo_app, ["delete-all", "--yes", "--output", "json"])
    assert result.exit_code != 0
    assert json.loads(result.stdout)["response"]["status"] != 0
