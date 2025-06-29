import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.keymatch import keymatch_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_keymatch_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for KeyMatches.
    """
    # 1) Create a new keymatch
    term = f"term-{uuid.uuid4().hex[:8]}"
    query = "fess"
    max_size = "10"
    boost = "100.0"
    version_no = "1"
    result = runner.invoke(
        keymatch_app,
        ["create", "--term", term, "--query", query, "--max-size", max_size, "--boost", boost, "--version-no", version_no, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    keymatch_id = create_resp["response"].get("id")
    assert keymatch_id, "No keymatch ID returned on create"

    # 2) Retrieve the created keymatch
    result = runner.invoke(
        keymatch_app,
        ["get", keymatch_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == keymatch_id
    assert setting.get("term") == term

    # 3) Update the keymatch's boost
    new_boost = "200.0"
    result = runner.invoke(
        keymatch_app,
        ["update", keymatch_id, "--boost", new_boost, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated boost
    result = runner.invoke(
        keymatch_app,
        ["get", keymatch_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("boost") == float(new_boost)

    # 5) List keymatches and ensure the updated keymatch appears
    result = runner.invoke(
        keymatch_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert keymatch_id in ids

    # 6) Delete the keymatch
    result = runner.invoke(
        keymatch_app,
        ["delete", keymatch_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        keymatch_app,
        ["get", keymatch_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve keymatch" in result.stdout.lower()
