import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.fileconfig import fileconfig_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_fileconfig_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for FileConfigs.
    """
    # 1) Create a new fileconfig
    unique_name = f"file-{uuid.uuid4().hex[:8]}"
    path = f"file:/{unique_name}/"
    result = runner.invoke(
        fileconfig_app,
        ["create", "--name", unique_name, "--path", path, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    fileconfig_id = create_resp["response"].get("id")
    assert fileconfig_id, "No fileconfig ID returned on create"

    # 2) Retrieve the created fileconfig
    result = runner.invoke(
        fileconfig_app,
        ["get", fileconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == fileconfig_id
    assert setting.get("name") == unique_name

    # 3) Update the fileconfig's description
    new_description = "test description"
    result = runner.invoke(
        fileconfig_app,
        ["update", fileconfig_id, "--description", new_description, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated description
    result = runner.invoke(
        fileconfig_app,
        ["get", fileconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("description") == new_description

    # 5) List fileconfigs and ensure the updated fileconfig appears
    result = runner.invoke(
        fileconfig_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert fileconfig_id in ids

    # 6) Delete the fileconfig
    result = runner.invoke(
        fileconfig_app,
        ["delete", fileconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        fileconfig_app,
        ["get", fileconfig_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve fileconfig" in result.stdout.lower()
