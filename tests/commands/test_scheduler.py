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
