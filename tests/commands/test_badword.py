import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.badword import badword_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_badword_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for BadWords.
    """
    # 1) Create a new badword
    suggest_word = f"badword-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        badword_app,
        ["create", "--suggest-word", suggest_word, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    badword_id = create_resp["response"].get("id")
    assert badword_id, "No badword ID returned on create"

    # 2) Retrieve the created badword
    result = runner.invoke(
        badword_app,
        ["get", badword_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == badword_id
    assert setting.get("suggest_word") == suggest_word

    # 3) Update the badword's suggest_word
    new_suggest_word = f"updated-{suggest_word}"
    result = runner.invoke(
        badword_app,
        ["update", badword_id, "--suggest-word", new_suggest_word, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated suggest_word
    result = runner.invoke(
        badword_app,
        ["get", badword_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("suggest_word") == new_suggest_word

    # 5) List badwords and ensure the updated badword appears
    result = runner.invoke(
        badword_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert badword_id in ids

    # 6) Delete the badword
    result = runner.invoke(
        badword_app,
        ["delete", badword_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        badword_app,
        ["get", badword_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve badword" in result.stdout.lower()
