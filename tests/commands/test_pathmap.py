import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.pathmap import pathmap_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_pathmap_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for PathMaps.
    """
    # 1) Create a new pathmap
    regex = f"https://{uuid.uuid4().hex[:8]}.com/"
    process_type = "CRAWLING"
    replacement = "https://fess.codelibs.org/"
    result = runner.invoke(
        pathmap_app,
        ["create", "--regex", regex, "--process-type", process_type, "--replacement", replacement, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    pathmap_id = create_resp["response"].get("id")
    assert pathmap_id, "No pathmap ID returned on create"

    # 2) Retrieve the created pathmap
    result = runner.invoke(
        pathmap_app,
        ["get", pathmap_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == pathmap_id
    assert setting.get("regex") == regex

    # 3) Update the pathmap's replacement
    new_replacement = "https://www.n2sm.net/"
    result = runner.invoke(
        pathmap_app,
        ["update", pathmap_id, "--replacement", new_replacement, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated replacement
    result = runner.invoke(
        pathmap_app,
        ["get", pathmap_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("replacement") == new_replacement

    # 5) List pathmaps and ensure the updated pathmap appears
    result = runner.invoke(
        pathmap_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert pathmap_id in ids

    # 6) Delete the pathmap
    result = runner.invoke(
        pathmap_app,
        ["delete", pathmap_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        pathmap_app,
        ["get", pathmap_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve pathmap" in result.stdout.lower()
