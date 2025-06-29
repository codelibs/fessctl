import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.dataconfig import dataconfig_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_dataconfig_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for DataConfigs.
    """
    # 1) Create a new dataconfig
    unique_name = f"data-{uuid.uuid4().hex[:8]}"
    handler_name = "csv"
    result = runner.invoke(
        dataconfig_app,
        ["create", "--name", unique_name, "--handler-name", handler_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    dataconfig_id = create_resp["response"].get("id")
    assert dataconfig_id, "No dataconfig ID returned on create"

    # 2) Retrieve the created dataconfig
    result = runner.invoke(
        dataconfig_app,
        ["get", dataconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == dataconfig_id
    assert setting.get("name") == unique_name

    # 3) Update the dataconfig's description
    new_description = "test description"
    result = runner.invoke(
        dataconfig_app,
        ["update", dataconfig_id, "--description", new_description, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated description
    result = runner.invoke(
        dataconfig_app,
        ["get", dataconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("description") == new_description

    # 5) List dataconfigs and ensure the updated dataconfig appears
    result = runner.invoke(
        dataconfig_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert dataconfig_id in ids

    # 6) Delete the dataconfig
    result = runner.invoke(
        dataconfig_app,
        ["delete", dataconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        dataconfig_app,
        ["get", dataconfig_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve dataconfig" in result.stdout.lower()
