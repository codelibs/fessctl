import json
import uuid

import pytest
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClient, FessAPIClientError
from fessctl.commands.tagtype import tagtype_app
from fessctl.config.settings import Settings


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


@pytest.fixture(scope="module")
def tagtype_api(fess_service):
    """
    Skips when the Fess under test has no /api/admin/tagtype (not in Fess 15.9 or earlier).
    """
    try:
        result = FessAPIClient(Settings()).list_tagtypes()
    except FessAPIClientError:
        result = {}
    if result.get("response", {}).get("status") != 0:
        pytest.skip("Fess under test does not provide /api/admin/tagtype")


def test_tagtype_crud_flow(runner, tagtype_api):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for TagTypes.
    """
    # 1) Create a new tagtype
    name = f"tag-{uuid.uuid4().hex[:8]}"
    path = "https://www.example.com/doc.html"
    result = runner.invoke(
        tagtype_app,
        ["create", "--name", name, "--owner", "admin", "--path", path, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    tagtype_id = create_resp["response"].get("id")
    assert tagtype_id, "No tagtype ID returned on create"

    # 2) Retrieve the created tagtype
    result = runner.invoke(
        tagtype_app,
        ["get", "--output", "json", "--", tagtype_id]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == tagtype_id
    assert setting.get("name") == name
    assert setting.get("paths") == path

    # 3) Update the sort order; the paths must be kept
    result = runner.invoke(
        tagtype_app,
        ["update", "--sort-order", "5", "--output", "json", "--", tagtype_id]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0
    tagtype_id = update_resp["response"].get("id") or tagtype_id

    # 4) Retrieve again and verify the update
    result = runner.invoke(
        tagtype_app,
        ["get", "--output", "json", "--", tagtype_id]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    setting_after = json.loads(result.stdout)["response"].get("setting", {})
    assert setting_after.get("sort_order") == 5
    assert setting_after.get("paths") == path

    # 5) List tagtypes and ensure the tagtype appears
    result = runner.invoke(
        tagtype_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    ids = [g.get("id") for g in list_resp["response"].get("settings", [])]
    assert tagtype_id in ids

    # 6) Delete the tagtype
    result = runner.invoke(
        tagtype_app,
        ["delete", "--output", "json", "--", tagtype_id]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        tagtype_app,
        ["get", "--", tagtype_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve tagtype" in result.stdout.lower()
