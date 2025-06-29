import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.duplicatehost import duplicatehost_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_duplicatehost_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for DuplicateHosts.
    """
    # 1) Create a new duplicatehost
    regular_name = f"regular-{uuid.uuid4().hex[:8]}.com"
    duplicate_name = f"duplicate-{uuid.uuid4().hex[:8]}.com"
    sort_order = "0"
    result = runner.invoke(
        duplicatehost_app,
        ["create", "--regular-name", regular_name, "--duplicate-host-name", duplicate_name, "--sort-order", sort_order, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    duplicatehost_id = create_resp["response"].get("id")
    assert duplicatehost_id, "No duplicatehost ID returned on create"

    # 2) Retrieve the created duplicatehost
    result = runner.invoke(
        duplicatehost_app,
        ["get", duplicatehost_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == duplicatehost_id
    assert setting.get("regular_name") == regular_name

    # 3) Update the duplicatehost's sort_order
    new_sort_order = "10"
    result = runner.invoke(
        duplicatehost_app,
        ["update", duplicatehost_id, "--sort-order", new_sort_order, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated sort_order
    result = runner.invoke(
        duplicatehost_app,
        ["get", duplicatehost_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("sort_order") == int(new_sort_order)

    # 5) List duplicatehosts and ensure the updated duplicatehost appears
    result = runner.invoke(
        duplicatehost_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert duplicatehost_id in ids

    # 6) Delete the duplicatehost
    result = runner.invoke(
        duplicatehost_app,
        ["delete", duplicatehost_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        duplicatehost_app,
        ["get", duplicatehost_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve duplicatehost" in result.stdout.lower()
