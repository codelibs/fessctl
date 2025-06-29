import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.elevateword import elevateword_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_elevateword_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for ElevateWords.
    """
    # 1) Create a new elevateword
    suggest_word = f"elevate-{uuid.uuid4().hex[:8]}"
    boost = "10.0"
    version_no = "1"
    result = runner.invoke(
        elevateword_app,
        ["create", "--suggest-word", suggest_word, "--boost", boost, "--version-no", version_no, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    elevateword_id = create_resp["response"].get("id")
    assert elevateword_id, "No elevateword ID returned on create"

    # 2) Retrieve the created elevateword
    result = runner.invoke(
        elevateword_app,
        ["get", elevateword_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == elevateword_id
    assert setting.get("suggest_word") == suggest_word

    # 3) Update the elevateword's boost
    new_boost = "20.0"
    result = runner.invoke(
        elevateword_app,
        ["update", elevateword_id, "--boost", new_boost, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated boost
    result = runner.invoke(
        elevateword_app,
        ["get", elevateword_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("boost") == float(new_boost)

    # 5) List elevatewords and ensure the updated elevateword appears
    result = runner.invoke(
        elevateword_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert elevateword_id in ids

    # 6) Delete the elevateword
    result = runner.invoke(
        elevateword_app,
        ["delete", elevateword_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        elevateword_app,
        ["get", elevateword_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve elevateword" in result.stdout.lower()
