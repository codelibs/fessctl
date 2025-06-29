import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.fileauth import fileauth_app
from fessctl.commands.fileconfig import fileconfig_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


@pytest.fixture(scope="function")
def temp_fileconfig(runner):
    """
    Provides a temporary fileconfig for tests that require one.
    """
    unique_name = f"temp-fileconfig-{uuid.uuid4().hex[:8]}"
    path = f"file:/{unique_name}/"
    result = runner.invoke(
        fileconfig_app,
        ["create", "--name", unique_name, "--path", path, "--output", "json"]
    )
    assert result.exit_code == 0, f"Failed to create temp fileconfig: {result.stdout}"
    fileconfig_id = json.loads(result.stdout)["response"]["id"]
    yield fileconfig_id
    runner.invoke(fileconfig_app, ["delete", fileconfig_id])


def test_fileauth_crud_flow(runner, fess_service, temp_fileconfig):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for FileAuths.
    """
    # 1) Create a new fileauth
    username = f"user-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        fileauth_app,
        ["create", "--username", username, "--file-config-id", temp_fileconfig, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    fileauth_id = create_resp["response"].get("id")
    assert fileauth_id, "No fileauth ID returned on create"

    # 2) Retrieve the created fileauth
    result = runner.invoke(
        fileauth_app,
        ["get", fileauth_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == fileauth_id
    assert setting.get("username") == username

    # 3) Update the fileauth's password
    new_password = "new_password"
    result = runner.invoke(
        fileauth_app,
        ["update", fileauth_id, "--password", new_password, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated password
    result = runner.invoke(
        fileauth_app,
        ["get", fileauth_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("password") == new_password

    # 5) List fileauths and ensure the updated fileauth appears
    result = runner.invoke(
        fileauth_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert fileauth_id in ids

    # 6) Delete the fileauth
    result = runner.invoke(
        fileauth_app,
        ["delete", fileauth_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        fileauth_app,
        ["get", fileauth_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve fileauth" in result.stdout.lower()
