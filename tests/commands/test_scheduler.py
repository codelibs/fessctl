import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.scheduler import scheduler_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_scheduler_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for Schedulers.
    """
    # 1) Create a new scheduler
    unique_name = f"schedule-{uuid.uuid4().hex[:8]}"
    target = "all"
    script_type = "groovy"
    cron = "0 12 * * *"
    result = runner.invoke(
        scheduler_app,
        ["create", "--name", unique_name, "--target", target, "--script-type", script_type, "--cron-expression", cron, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    scheduler_id = create_resp["response"].get("id")
    assert scheduler_id, "No scheduler ID returned on create"

    # 2) Retrieve the created scheduler
    result = runner.invoke(
        scheduler_app,
        ["get", scheduler_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == scheduler_id
    assert setting.get("name") == unique_name

    # 3) Update the scheduler's cron_expression
    new_cron = "0 13 * * *"
    result = runner.invoke(
        scheduler_app,
        ["update", scheduler_id, "--cron-expression", new_cron, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated cron_expression
    result = runner.invoke(
        scheduler_app,
        ["get", scheduler_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("cron_expression") == new_cron

    # 5) List schedulers and ensure the updated scheduler appears
    result = runner.invoke(
        scheduler_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert scheduler_id in ids

    # 6) Delete the scheduler
    result = runner.invoke(
        scheduler_app,
        ["delete", scheduler_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        scheduler_app,
        ["get", scheduler_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve scheduler" in result.stdout.lower()


def test_scheduler_start_stop(runner, fess_service):
    """
    Tests the start and stop commands for Schedulers.
    Creates a scheduler, starts it, stops it, then cleans up.
    """
    # 1) Create a new scheduler for testing start/stop
    unique_name = f"schedule-startstop-{uuid.uuid4().hex[:8]}"
    target = "all"
    script_type = "groovy"
    cron = "0 0 * * *"  # Daily at midnight
    result = runner.invoke(
        scheduler_app,
        ["create", "--name", unique_name, "--target", target, "--script-type", script_type, "--cron-expression", cron, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    scheduler_id = create_resp["response"].get("id")
    assert scheduler_id, "No scheduler ID returned on create"

    try:
        # 2) Start the scheduler
        result = runner.invoke(
            scheduler_app,
            ["start", scheduler_id, "--output", "json"]
        )
        assert result.exit_code == 0, f"Start failed: {result.stdout}"
        start_resp = json.loads(result.stdout)
        assert start_resp.get("response", {}).get("status") == 0

        # 3) Stop the scheduler
        result = runner.invoke(
            scheduler_app,
            ["stop", scheduler_id, "--output", "json"]
        )
        assert result.exit_code == 0, f"Stop failed: {result.stdout}"
        stop_resp = json.loads(result.stdout)
        assert stop_resp.get("response", {}).get("status") == 0

    finally:
        # 4) Clean up - delete the scheduler
        runner.invoke(
            scheduler_app,
            ["delete", scheduler_id, "--output", "json"]
        )


def test_scheduler_start_text_output(runner, fess_service):
    """
    Tests the start command with text output format.
    """
    # Create a scheduler
    unique_name = f"schedule-text-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        scheduler_app,
        ["create", "--name", unique_name, "--target", "all", "--script-type", "groovy", "--cron-expression", "0 0 * * *", "--output", "json"]
    )
    assert result.exit_code == 0
    scheduler_id = json.loads(result.stdout)["response"]["id"]

    try:
        # Start with text output
        result = runner.invoke(
            scheduler_app,
            ["start", scheduler_id, "--output", "text"]
        )
        assert result.exit_code == 0
        assert "started successfully" in result.stdout.lower()

        # Stop with text output
        result = runner.invoke(
            scheduler_app,
            ["stop", scheduler_id, "--output", "text"]
        )
        assert result.exit_code == 0
        assert "stopped successfully" in result.stdout.lower()

    finally:
        runner.invoke(scheduler_app, ["delete", scheduler_id])


def test_scheduler_start_yaml_output(runner, fess_service):
    """
    Tests the start command with YAML output format.
    """
    # Create a scheduler
    unique_name = f"schedule-yaml-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        scheduler_app,
        ["create", "--name", unique_name, "--target", "all", "--script-type", "groovy", "--cron-expression", "0 0 * * *", "--output", "json"]
    )
    assert result.exit_code == 0
    scheduler_id = json.loads(result.stdout)["response"]["id"]

    try:
        # Start with YAML output
        result = runner.invoke(
            scheduler_app,
            ["start", scheduler_id, "--output", "yaml"]
        )
        assert result.exit_code == 0
        assert "response:" in result.stdout or "status:" in result.stdout

    finally:
        runner.invoke(scheduler_app, ["delete", scheduler_id])


def test_scheduler_start_nonexistent(runner, fess_service):
    """
    Tests starting a non-existent scheduler returns an error.
    """
    result = runner.invoke(
        scheduler_app,
        ["start", "nonexistent-scheduler-id"]
    )
    assert result.exit_code != 0
    assert "failed to start scheduler" in result.stdout.lower()


def test_scheduler_stop_nonexistent(runner, fess_service):
    """
    Tests stopping a non-existent scheduler returns an error.
    """
    result = runner.invoke(
        scheduler_app,
        ["stop", "nonexistent-scheduler-id"]
    )
    assert result.exit_code != 0
    assert "failed to stop scheduler" in result.stdout.lower()
