import json
import time
import uuid

import pytest
from typer.testing import CliRunner

from fessctl.cli import app
from fessctl.commands.searchlist import searchlist_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def _hits(runner, query):
    result = runner.invoke(searchlist_app, ["search", query, "--output", "json"])
    assert result.exit_code == 0, f"Search failed: {result.stdout}"
    return json.loads(result.stdout)["response"]["record_count"]


def _wait_for_count(runner, query, count, timeout=30):
    deadline = time.time() + timeout
    while _hits(runner, query) != count:
        assert time.time() < deadline, f"'{query}' did not reach {count} hits"
        time.sleep(1)


@pytest.fixture
def token(runner, fess_service):
    """
    A unique search token for the documents of one test. Bulk results report the
    index _id, not the doc_id, so the documents are removed by query afterwards.
    """
    value = f"fessctl{uuid.uuid4().hex}"
    yield value
    result = runner.invoke(searchlist_app, ["delete-by-query", value, "--yes"])
    assert result.exit_code == 0, f"Cleanup failed: {result.stdout}"
    _wait_for_count(runner, value, 0)


def _doc(token, name, **extra):
    return {"url": f"http://{token}.invalid/{name}", "title": f"{token} {name}",
            "content": f"{token} content of {name}", **extra}


def test_documents_bulk_json_array(runner, token, tmp_path):
    path = tmp_path / "docs.json"
    path.write_text(json.dumps([_doc(token, "a"), _doc(token, "b", label=["fessctl-it"])]))

    result = runner.invoke(app, ["documents", "bulk", str(path), "--output", "json"])
    assert result.exit_code == 0, f"Bulk failed: {result.stdout}"
    resp = json.loads(result.stdout)["response"]
    assert resp.get("status") == 0
    assert [item["result"] for item in resp["items"]] == ["CREATED", "CREATED"]

    _wait_for_count(runner, token, 2)


def test_documents_bulk_ndjson_and_stdin(runner, token):
    ndjson = "\n".join(json.dumps(_doc(token, name)) for name in ("a", "b", "c")) + "\n"

    result = runner.invoke(app, ["documents", "bulk", "-"], input=ndjson)
    assert result.exit_code == 0, f"Bulk failed: {result.stdout}"
    assert "3 document(s) indexed." in result.stdout

    _wait_for_count(runner, token, 3)


def test_documents_bulk_partial_failure(runner, token, tmp_path):
    # a document whose field cannot be mapped fails alone; the others are indexed
    path = tmp_path / "docs.ndjson"
    path.write_text("\n".join(json.dumps(d) for d in (_doc(token, "good"), _doc(token, "bad", mimetype={"a": 1}))))

    result = runner.invoke(app, ["documents", "bulk", str(path)])
    assert result.exit_code != 0
    assert "CREATED" in result.stdout
    assert "BAD_REQUEST" in result.stdout

    _wait_for_count(runner, token, 1)


def test_documents_bulk_validation_error(runner, fess_service, tmp_path):
    path = tmp_path / "docs.json"
    path.write_text(json.dumps([{"title": "no url"}]))

    result = runner.invoke(app, ["documents", "bulk", str(path)])
    assert result.exit_code != 0
    assert "failed to index documents" in result.stdout.lower()


def test_documents_bulk_missing_file(runner, fess_service, tmp_path):
    result = runner.invoke(app, ["documents", "bulk", str(tmp_path / "missing.json")])
    assert result.exit_code != 0
    assert "cannot read documents" in result.stdout.lower()
