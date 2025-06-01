import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.role import role_app


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_role_crud_flow(runner, fess_service):
    # 1) Create a new role
    unique_name = f"role-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        role_app,
        ["create", unique_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    role_id = create_resp["response"].get("id")
    assert role_id, "No role ID returned on create"

    # 2) Retrieve the created role
    result = runner.invoke(
        role_app,
        ["get", role_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == role_id
    assert setting.get("name") == unique_name
    # Newly created role should have no attributes by default
    assert setting.get("attributes", {}) == {}

    # 3) Update the role's attributes
    result = runner.invoke(
        role_app,
        ["update", role_id, "--attribute", "key1=val1", "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated attributes
    result = runner.invoke(
        role_app,
        ["get", role_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    attributes_after = setting_after.get("attributes", {})
    assert attributes_after.get("key1") == "val1"

    # 5) List roles and ensure the updated role appears with the attribute
    result = runner.invoke(
        role_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [r.get("id") for r in settings]
    assert role_id in ids
    # find the entry for our role
    matching = [r for r in settings if r.get("id") == role_id]
    assert matching, "Created role not found in list"
    attrs_listed = matching[0].get("attributes", {})
    assert attrs_listed.get("key1") == "val1"

    # 6) Delete the role
    result = runner.invoke(
        role_app,
        ["delete", role_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        role_app,
        ["get", role_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve role" in result.stdout.lower()


def test_getbyname_role(runner, fess_service):
    """
    Verify that getbyname:<name> behaves the same as get:<base64(name)>.
    """
    unique_name = f"role-{uuid.uuid4().hex[:8]}"
    create_res = runner.invoke(
        role_app,
        ["create", unique_name, "--output", "json"]
    )
    assert create_res.exit_code == 0
    role_id = json.loads(create_res.stdout)["response"]["id"]

    result = runner.invoke(
        role_app,
        ["getbyname", unique_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"getbyname failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp["response"]["status"] == 0
    setting = get_resp["response"]["setting"]
    assert setting["id"] == role_id
    assert setting["name"] == unique_name

    # Cleanup
    runner.invoke(role_app, ["delete", role_id, "--output", "json"])
