import uuid
import json
import pytest
from typer.testing import CliRunner

from fessctl.commands.boostdoc import boostdoc_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_boostdoc_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for BoostDocs.
    """
    # 1) Create a new boostdoc
    url_expr = f"https://example.com/{uuid.uuid4().hex[:8]}"
    boost_expr = "10.0"
    sort_order = "0"
    result = runner.invoke(
        boostdoc_app,
        ["create", "--url-expr", url_expr, "--boost-expr", boost_expr, "--sort-order", sort_order, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    boostdoc_id = create_resp["response"].get("id")
    assert boostdoc_id, "No boostdoc ID returned on create"

    # 2) Retrieve the created boostdoc
    result = runner.invoke(
        boostdoc_app,
        ["get", boostdoc_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == boostdoc_id
    assert setting.get("url_expr") == url_expr

    # 3) Update the boostdoc's boost_expr
    new_boost_expr = "20.0"
    result = runner.invoke(
        boostdoc_app,
        ["update", boostdoc_id, "--boost-expr", new_boost_expr, "--output", "json"]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated boost_expr
    result = runner.invoke(
        boostdoc_app,
        ["get", boostdoc_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("boost_expr") == new_boost_expr

    # 5) List boostdocs and ensure the updated boostdoc appears
    result = runner.invoke(
        boostdoc_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert boostdoc_id in ids

    # 6) Delete the boostdoc
    result = runner.invoke(
        boostdoc_app,
        ["delete", boostdoc_id, "--output", "json"]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        boostdoc_app,
        ["get", boostdoc_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve boostdoc" in result.stdout.lower()
