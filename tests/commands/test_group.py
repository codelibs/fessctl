import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.group import group_app


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


def test_group_crud_flow(runner, fess_service):
    # 1) Create a new group
    unique_name = f"group-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        group_app,
        ["create", unique_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    group_id = create_resp["response"].get("id")
    assert group_id, "No group ID returned on create"

    # 2) Retrieve the created group
    result = runner.invoke(
        group_app,
        ["get", group_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == group_id
    assert setting.get("name") == unique_name
    # Newly created group should have no attributes by default
    assert setting.get("attributes", {}) == {}

    # 3) Update the group's attributes
    result = runner.invoke(
        group_app,
        ["update", group_id, "--attribute", "key1=val1", "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated attributes
    result = runner.invoke(
        group_app,
        ["get", group_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    attributes_after = setting_after.get("attributes", {})
    assert attributes_after.get("key1") == "val1"

    # 5) List groups and ensure the updated group appears with the attribute
    result = runner.invoke(
        group_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert group_id in ids
    # find the entry for our group
    matching = [g for g in settings if g.get("id") == group_id]
    assert matching, "Created group not found in list"
    attrs_listed = matching[0].get("attributes", {})
    assert attrs_listed.get("key1") == "val1"

    # 6) Delete the group
    result = runner.invoke(
        group_app,
        ["delete", group_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        group_app,
        ["get", group_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve group" in result.stdout.lower()


def test_getbyname_group(runner, fess_service):
    """
    Verify that getbyname:<name> behaves the same as get:<base64(name)>.
    """
    unique_name = f"group-{uuid.uuid4().hex[:8]}"
    create_res = runner.invoke(
        group_app,
        ["create", unique_name, "--output", "json"]
    )
    assert create_res.exit_code == 0
    group_id = json.loads(create_res.stdout)["response"]["id"]

    result = runner.invoke(
        group_app,
        ["getbyname", unique_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"getbyname failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp["response"]["status"] == 0
    setting = get_resp["response"]["setting"]
    assert setting["id"] == group_id
    assert setting["name"] == unique_name

    runner.invoke(group_app, ["delete", group_id, "--output", "json"])
