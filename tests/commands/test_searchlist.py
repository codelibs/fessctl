import json
import time
import uuid

import pytest
from typer.testing import CliRunner

from conftest import fess_version_at_least
from fessctl.commands.searchlist import searchlist_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def _search(runner, query, **options):
    args = ["search", query, "--output", "json"]
    for key, value in options.items():
        args += [f"--{key}", str(value)]
    result = runner.invoke(searchlist_app, args)
    assert result.exit_code == 0, f"Search failed: {result.stdout}"
    return json.loads(result.stdout)["response"]


def _wait_for_count(runner, query, count, timeout=30):
    """
    Newly indexed documents become searchable only after an index refresh,
    so poll until the query returns the expected number of hits.
    """
    deadline = time.time() + timeout
    while True:
        response = _search(runner, query)
        if response.get("record_count") == count:
            return response
        assert time.time() < deadline, f"'{query}' still returns {response.get('record_count')} hits, wanted {count}"
        time.sleep(1)


@pytest.fixture
def token(runner, fess_service):
    """
    A unique search token for the documents of one test. Everything matching it
    is removed afterwards, even when the test fails.
    """
    value = f"fessctl{uuid.uuid4().hex}"
    yield value
    result = runner.invoke(searchlist_app, ["delete-by-query", value, "--yes"])
    assert result.exit_code == 0, f"Cleanup failed: {result.stdout}"
    _wait_for_count(runner, value, 0)


def _create(runner, token, name, *extra):
    result = runner.invoke(searchlist_app, [
        "create", "--url", f"http://{token}.invalid/{name}", "--title", f"{token} {name}",
        "--role", "Rguest", "--content", f"{token} content of {name}", *extra, "--output", "json",
    ])
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    resp = json.loads(result.stdout)["response"]
    assert resp.get("status") == 0
    assert resp.get("created") is True
    return resp["id"]


def test_searchlist_create_search_get_update_delete(runner, token):
    doc_id = _create(runner, token, "one", "--label", "fessctl-it", "--field", "mimetype=text/plain")

    response = _wait_for_count(runner, token, 1)
    assert response["docs"][0]["doc_id"] == doc_id

    result = runner.invoke(searchlist_app, ["get", doc_id, "--output", "json"])
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    doc = json.loads(result.stdout)["response"]["doc"]
    assert doc["url"] == f"http://{token}.invalid/one"
    assert doc["role"] == ["Rguest"]
    assert doc["boost"] == 1.0
    assert doc["label"] == ["fessctl-it"]
    assert doc["mimetype"] == "text/plain"

    result = runner.invoke(searchlist_app, ["get", doc_id])
    assert result.exit_code == 0
    assert f"| doc_id | {doc_id} |" in result.stdout

    # update changes only the given fields; the others are kept
    result = runner.invoke(searchlist_app, ["update", doc_id, "--title", f"{token} renamed", "--boost", "2.5"])
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    result = runner.invoke(searchlist_app, ["get", doc_id, "--output", "json"])
    updated = json.loads(result.stdout)["response"]["doc"]
    assert updated["title"] == f"{token} renamed"
    assert updated["boost"] == 2.5
    assert updated["url"] == doc["url"]
    assert updated["role"] == ["Rguest"]
    assert updated["label"] == ["fessctl-it"]
    assert updated["content"] == doc["content"]

    result = runner.invoke(searchlist_app, ["delete", doc_id])
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    _wait_for_count(runner, token, 0)

    result = runner.invoke(searchlist_app, ["get", doc_id])
    assert result.exit_code != 0
    assert "failed to retrieve document" in result.stdout.lower()


def test_searchlist_search_paging(runner, token):
    for name in ("a", "b", "c"):
        _create(runner, token, name)
    _wait_for_count(runner, token, 3)

    first = _search(runner, token, size=2)
    assert first["page_size"] == 2
    assert len(first["docs"]) == 2
    assert first["record_count"] == 3

    second = _search(runner, token, size=2, start=2)
    assert len(second["docs"]) == 1
    seen = {d["doc_id"] for d in first["docs"]} | {d["doc_id"] for d in second["docs"]}
    assert len(seen) == 3

    result = runner.invoke(searchlist_app, ["search", token])
    assert result.exit_code == 0
    assert "of 3)" in result.stdout


def test_searchlist_delete_by_query(runner, token):
    for name in ("a", "b"):
        _create(runner, token, name)
    _wait_for_count(runner, token, 2)

    # a declined confirmation deletes nothing
    result = runner.invoke(searchlist_app, ["delete-by-query", token], input="n\n")
    assert result.exit_code != 0
    assert _search(runner, token)["record_count"] == 2

    result = runner.invoke(searchlist_app, ["delete-by-query", token, "--yes", "--output", "json"])
    assert result.exit_code == 0, f"Delete by query failed: {result.stdout}"
    resp = json.loads(result.stdout)["response"]
    assert resp.get("status") == 0
    assert resp.get("count") == 2
    _wait_for_count(runner, token, 0)


def test_searchlist_get_not_found(runner, fess_service):
    result = runner.invoke(searchlist_app, ["get", "no-such-doc-id"])
    assert result.exit_code != 0
    assert "failed to retrieve document" in result.stdout.lower()


def test_searchlist_update_not_found(runner, fess_service):
    result = runner.invoke(searchlist_app, ["update", "no-such-doc-id", "--title", "x"])
    assert result.exit_code != 0
    assert "failed to retrieve document" in result.stdout.lower()


def test_searchlist_create_validation_error(runner, fess_service):
    # url, title, role and boost are required; a non-numeric long field is refused
    result = runner.invoke(searchlist_app, [
        "create", "--url", "http://fessctl-invalid.invalid/", "--title", "t", "--role", "Rguest",
        "--field", "click_count=abc",
    ])
    assert result.exit_code != 0
    assert "failed to create document" in result.stdout.lower()


def test_searchlist_delete_not_found(runner, fess_service):
    if not fess_version_at_least(15, 9):
        pytest.skip("Fess before 15.9 answers a delete of an unknown doc_id with success")
    result = runner.invoke(searchlist_app, ["delete", "no-such-doc-id"])
    assert result.exit_code != 0
    assert "failed to delete document" in result.stdout.lower()


def test_searchlist_delete_by_query_blank_query_refused(runner, fess_service):
    result = runner.invoke(searchlist_app, ["delete-by-query", "", "--yes"])
    assert result.exit_code != 0
    assert "failed to delete documents" in result.stdout.lower()
