import json

import pytest
from typer.testing import CliRunner

from fessctl.commands.general import general_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def _get_setting(runner):
    result = runner.invoke(general_app, ["get", "--output", "json"])
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    resp = json.loads(result.stdout)
    assert resp.get("response", {}).get("status") == 0
    return resp["response"]["setting"]


def test_general_get(runner, fess_service):
    setting = _get_setting(runner)
    for key in ("day_for_cleanup", "crawling_thread_count", "failure_count_threshold", "csv_file_encoding"):
        assert key in setting

    result = runner.invoke(general_app, ["get"])
    assert result.exit_code == 0
    assert "| csv_file_encoding |" in result.stdout


def test_general_update_changes_only_the_given_settings(runner, fess_service):
    before = _get_setting(runner)
    new_purge_days = 45 if before["purge_job_log_day"] != 45 else 46
    new_notice = "fessctl-test" if before["notification_login"] != "fessctl-test" else "fessctl-test2"
    try:
        result = runner.invoke(general_app, [
            "update",
            "--set", f"purge_job_log_day={new_purge_days}",
            "--set", f"notification_login={new_notice}",
        ])
        assert result.exit_code == 0, f"Update failed: {result.stdout}"

        after = _get_setting(runner)
        assert after["purge_job_log_day"] == new_purge_days
        assert after["notification_login"] == new_notice
        unchanged = {k: v for k, v in after.items() if k not in ("purge_job_log_day", "notification_login")}
        assert unchanged == {k: v for k, v in before.items() if k in unchanged}
        assert set(after) == set(before)
    finally:
        runner.invoke(general_app, [
            "update",
            "--set", f"purge_job_log_day={before['purge_job_log_day']}",
            "--set", f"notification_login={before['notification_login']}",
        ])

    assert _get_setting(runner) == before


def test_general_update_rejects_unknown_setting(runner, fess_service):
    result = runner.invoke(general_app, ["update", "--set", "no_such_setting=1"])
    assert result.exit_code == 2


def test_general_update_validation_error(runner, fess_service):
    before = _get_setting(runner)
    result = runner.invoke(general_app, ["update", "--set", "day_for_cleanup=99999"])
    assert result.exit_code != 0
    assert "failed to update general settings" in result.stdout.lower()
    assert _get_setting(runner) == before
