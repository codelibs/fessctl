import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.user import user_app


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_user_crud_flow(runner, fess_service):
    """
    Integration test for user CRUD operations against a running Fess instance.
    Assumes FessAPIClient(Settings()) reads FESS_ENDPOINT and FESS_ACCESS_TOKEN
    from environment, as set by the fess_service fixture.
    """
    # 1) Create a new user
    unique_name = f"user-{uuid.uuid4().hex[:8]}"
    password = "InitialPass123"
    result = runner.invoke(
        user_app,
        ["create", unique_name, password, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    user_id = create_resp["response"].get("id")
    assert user_id, "No user ID returned on create"

    # 2) Retrieve the created user
    result = runner.invoke(
        user_app,
        ["get", user_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == user_id
    assert setting.get("name") == unique_name
    # Newly created user should have no attributes, roles, or groups by default
    assert setting.get("attributes", {}) == {}
    assert setting.get("roles", []) == []
    assert setting.get("groups", []) == []

    # 3) Update the user's password, attributes, roles, and groups
    new_password = "NewPass456"
    attribute_kv = "key1=val1"
    role_name = "roleA"
    group_name = "groupA"
    result = runner.invoke(
        user_app,
        [
            "update", user_id,
            "--password", new_password,
            "--attribute", attribute_kv,
            "--role", role_name,
            "--group", group_name,
            "--output", "json"
        ]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated fields
    result = runner.invoke(
        user_app,
        ["get", user_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    # Attributes should include key1=val1
    attributes_after = setting_after.get("attributes", {})
    assert attributes_after.get("key1") == "val1"
    # Roles should include roleA
    roles_after = setting_after.get("roles", [])
    assert role_name in roles_after
    # Groups should include groupA
    groups_after = setting_after.get("groups", [])
    assert group_name in groups_after

    # 5) List users and ensure the updated user appears with the correct fields
    result = runner.invoke(
        user_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    users = list_resp["response"].get("settings", [])
    ids = [u.get("id") for u in users]
    assert user_id in ids
    # find the entry for our user
    matching = [u for u in users if u.get("id") == user_id]
    assert matching, "Created user not found in list"
    listed = matching[0]
    assert listed.get("attributes", {}).get("key1") == "val1"
    assert role_name in listed.get("roles", [])
    assert group_name in listed.get("groups", [])

    # 6) Delete the user
    result = runner.invoke(
        user_app,
        ["delete", user_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        user_app,
        ["get", user_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve user" in result.stdout.lower()


def test_getbyname_user(runner, fess_service):
    """
    Verify that getbyname:<name> behaves the same as get:<base64(name)>.
    """
    unique_name = f"user-{uuid.uuid4().hex[:8]}"
    password = "SomePass789"
    create_res = runner.invoke(
        user_app,
        ["create", unique_name, password, "--output", "json"]
    )
    assert create_res.exit_code == 0
    user_id = json.loads(create_res.stdout)["response"]["id"]

    result = runner.invoke(
        user_app,
        ["getbyname", unique_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"getbyname failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp["response"]["status"] == 0
    setting = get_resp["response"]["setting"]
    assert setting["id"] == user_id
    assert setting["name"] == unique_name

    # Cleanup
    runner.invoke(user_app, ["delete", user_id, "--output", "json"])
