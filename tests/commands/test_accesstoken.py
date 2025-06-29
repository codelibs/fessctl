import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.accesstoken import accesstoken_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_accesstoken_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for AccessTokens.
    """
    # 1) Create a new accesstoken
    unique_name = f"token-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        accesstoken_app,
        ["create", "--name", unique_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    accesstoken_id = create_resp["response"].get("id")
    assert accesstoken_id, "No accesstoken ID returned on create"

    # 2) Retrieve the created accesstoken
    result = runner.invoke(
        accesstoken_app,
        ["get", accesstoken_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == accesstoken_id
    assert setting.get("name") == unique_name

    # 3) Update the accesstoken's permissions
    result = runner.invoke(
        accesstoken_app,
        ["update", accesstoken_id, "--permission", "admin", "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated permissions
    result = runner.invoke(
        accesstoken_app,
        ["get", accesstoken_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert "admin" in setting_after.get("permissions", "")

    # 5) List accesstokens and ensure the updated accesstoken appears
    result = runner.invoke(
        accesstoken_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert accesstoken_id in ids

    # 6) Delete the accesstoken
    result = runner.invoke(
        accesstoken_app,
        ["delete", accesstoken_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        accesstoken_app,
        ["get", accesstoken_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve accesstoken" in result.stdout.lower()
