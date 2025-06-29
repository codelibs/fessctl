import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.relatedcontent import relatedcontent_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_relatedcontent_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for RelatedContents.
    """
    # 1) Create a new relatedcontent
    term = f"term-{uuid.uuid4().hex[:8]}"
    content = "fess"
    result = runner.invoke(
        relatedcontent_app,
        ["create", "--term", term, "--content", content, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    relatedcontent_id = create_resp["response"].get("id")
    assert relatedcontent_id, "No relatedcontent ID returned on create"

    # 2) Retrieve the created relatedcontent
    result = runner.invoke(
        relatedcontent_app,
        ["get", relatedcontent_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == relatedcontent_id
    assert setting.get("term") == term

    # 3) Update the relatedcontent's content
    new_content = "n2sm"
    result = runner.invoke(
        relatedcontent_app,
        ["update", relatedcontent_id, "--content", new_content, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated content
    result = runner.invoke(
        relatedcontent_app,
        ["get", relatedcontent_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("content") == new_content

    # 5) List relatedcontents and ensure the updated relatedcontent appears
    result = runner.invoke(
        relatedcontent_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert relatedcontent_id in ids

    # 6) Delete the relatedcontent
    result = runner.invoke(
        relatedcontent_app,
        ["delete", relatedcontent_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        relatedcontent_app,
        ["get", relatedcontent_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve relatedcontent" in result.stdout.lower()
