import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.webauth import webauth_app
from fessctl.commands.webconfig import webconfig_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


@pytest.fixture(scope="function")
def temp_webconfig(runner):
    """
    Provides a temporary webconfig for tests that require one.
    """
    unique_name = f"temp-webconfig-{uuid.uuid4().hex[:8]}"
    url = f"https://{unique_name}.com/"
    result = runner.invoke(
        webconfig_app,
        ["create", "--name", unique_name, "--url", url, "--output", "json"]
    )
    assert result.exit_code == 0, f"Failed to create temp webconfig: {result.stdout}"
    webconfig_id = json.loads(result.stdout)["response"]["id"]
    yield webconfig_id
    runner.invoke(webconfig_app, ["delete", webconfig_id])


def test_webauth_crud_flow(runner, fess_service, temp_webconfig):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for WebAuths.
    """
    # 1) Create a new webauth
    username = f"user-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        webauth_app,
        ["create", "--username", username, "--web-config-id", temp_webconfig, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    webauth_id = create_resp["response"].get("id")
    assert webauth_id, "No webauth ID returned on create"

    # 2) Retrieve the created webauth
    result = runner.invoke(
        webauth_app,
        ["get", webauth_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == webauth_id
    assert setting.get("username") == username

    # 3) Update the webauth's password
    new_password = "new_password"
    result = runner.invoke(
        webauth_app,
        ["update", webauth_id, "--password", new_password, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated password
    result = runner.invoke(
        webauth_app,
        ["get", webauth_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("password") == new_password

    # 5) List webauths and ensure the updated webauth appears
    result = runner.invoke(
        webauth_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert webauth_id in ids

    # 6) Delete the webauth
    result = runner.invoke(
        webauth_app,
        ["delete", webauth_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        webauth_app,
        ["get", webauth_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve webauth" in result.stdout.lower()
