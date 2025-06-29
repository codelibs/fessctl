import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.relatedquery import relatedquery_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_relatedquery_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for RelatedQueries.
    """
    # 1) Create a new relatedquery
    term = f"term-{uuid.uuid4().hex[:8]}"
    queries = "fess"
    version_no = "1"
    result = runner.invoke(
        relatedquery_app,
        ["create", "--term", term, "--queries", queries, "--version-no", version_no, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    relatedquery_id = create_resp["response"].get("id")
    assert relatedquery_id, "No relatedquery ID returned on create"

    # 2) Retrieve the created relatedquery
    result = runner.invoke(
        relatedquery_app,
        ["get", relatedquery_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == relatedquery_id
    assert setting.get("term") == term

    # 3) Update the relatedquery's queries
    new_queries = "n2sm"
    result = runner.invoke(
        relatedquery_app,
        ["update", relatedquery_id, "--queries", new_queries, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated queries
    result = runner.invoke(
        relatedquery_app,
        ["get", relatedquery_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("queries") == new_queries

    # 5) List relatedqueries and ensure the updated relatedquery appears
    result = runner.invoke(
        relatedquery_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert relatedquery_id in ids

    # 6) Delete the relatedquery
    result = runner.invoke(
        relatedquery_app,
        ["delete", relatedquery_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        relatedquery_app,
        ["get", relatedquery_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve relatedquery" in result.stdout.lower()
