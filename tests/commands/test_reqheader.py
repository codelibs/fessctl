import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.reqheader import reqheader_app
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


def test_reqheader_crud_flow(runner, fess_service, temp_webconfig):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for ReqHeaders.
    """
    # 1) Create a new reqheader
    name = f"header-{uuid.uuid4().hex[:8]}"
    value = "test-value"
    result = runner.invoke(
        reqheader_app,
        ["create", "--name", name, "--value", value, "--web-config-id", temp_webconfig, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    reqheader_id = create_resp["response"].get("id")
    assert reqheader_id, "No reqheader ID returned on create"

    # 2) Retrieve the created reqheader
    result = runner.invoke(
        reqheader_app,
        ["get", reqheader_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == reqheader_id
    assert setting.get("name") == name

    # 3) Update the reqheader's value
    new_value = "new-test-value"
    result = runner.invoke(
        reqheader_app,
        ["update", reqheader_id, "--value", new_value, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated value
    result = runner.invoke(
        reqheader_app,
        ["get", reqheader_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("value") == new_value

    # 5) List reqheaders and ensure the updated reqheader appears
    result = runner.invoke(
        reqheader_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert reqheader_id in ids

    # 6) Delete the reqheader
    result = runner.invoke(
        reqheader_app,
        ["delete", reqheader_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        reqheader_app,
        ["get", reqheader_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve reqheader" in result.stdout.lower()
