import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.labeltype import labeltype_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_labeltype_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for LabelTypes.
    """
    # 1) Create a new labeltype
    name = f"label-{uuid.uuid4().hex[:8]}"
    value = f"value_{uuid.uuid4().hex[:8]}"
    version_no = "1"
    result = runner.invoke(
        labeltype_app,
        ["create", "--name", name, "--value", value, "--version-no", version_no, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    labeltype_id = create_resp["response"].get("id")
    assert labeltype_id, "No labeltype ID returned on create"

    # 2) Retrieve the created labeltype
    result = runner.invoke(
        labeltype_app,
        ["get", labeltype_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == labeltype_id
    assert setting.get("name") == name

    # 3) Update the labeltype's name
    new_name = f"new-{name}"
    result = runner.invoke(
        labeltype_app,
        ["update", labeltype_id, "--name", new_name, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated name
    result = runner.invoke(
        labeltype_app,
        ["get", labeltype_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("name") == new_name

    # 5) List labeltypes and ensure the updated labeltype appears
    result = runner.invoke(
        labeltype_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert labeltype_id in ids

    # 6) Delete the labeltype
    result = runner.invoke(
        labeltype_app,
        ["delete", labeltype_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        labeltype_app,
        ["get", labeltype_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve labeltype" in result.stdout.lower()
