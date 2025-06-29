import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.webconfig import webconfig_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_webconfig_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for WebConfigs.
    """
    # 1) Create a new webconfig
    unique_name = f"web-{uuid.uuid4().hex[:8]}"
    url = f"https://{unique_name}.com/"
    result = runner.invoke(
        webconfig_app,
        ["create", "--name", unique_name, "--url", url, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    webconfig_id = create_resp["response"].get("id")
    assert webconfig_id, "No webconfig ID returned on create"

    # 2) Retrieve the created webconfig
    result = runner.invoke(
        webconfig_app,
        ["get", webconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == webconfig_id
    assert setting.get("name") == unique_name

    # 3) Update the webconfig's description
    new_description = "test description"
    result = runner.invoke(
        webconfig_app,
        ["update", webconfig_id, "--description", new_description, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated description
    result = runner.invoke(
        webconfig_app,
        ["get", webconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("description") == new_description

    # 5) List webconfigs and ensure the updated webconfig appears
    result = runner.invoke(
        webconfig_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert webconfig_id in ids

    # 6) Delete the webconfig
    result = runner.invoke(
        webconfig_app,
        ["delete", webconfig_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        webconfig_app,
        ["get", webconfig_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve webconfig" in result.stdout.lower()
