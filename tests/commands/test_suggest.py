import json

import pytest
from typer.testing import CliRunner

from fessctl.commands.suggest import suggest_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def _word_counts(runner):
    result = runner.invoke(suggest_app, ["info", "--output", "json"])
    assert result.exit_code == 0, f"Info failed: {result.stdout}"
    resp = json.loads(result.stdout).get("response", {})
    assert resp.get("status") == 0
    setting = resp["setting"]
    assert all(isinstance(setting[k], int) for k in ("total_words_num", "document_words_num", "query_words_num"))
    return setting


def test_suggest_info_text(runner, fess_service):
    result = runner.invoke(suggest_app, ["info"])
    assert result.exit_code == 0, f"Info failed: {result.stdout}"
    assert "| total_words_num |" in result.stdout


@pytest.mark.parametrize("command", ["delete-query", "delete-document", "delete-all"])
def test_suggest_delete_asks_for_confirmation(runner, fess_service, command):
    result = runner.invoke(suggest_app, [command], input="n\n")
    assert result.exit_code != 0
    assert "[y/N]" in result.stdout


def test_suggest_delete(runner, fess_service):
    """
    The suggest index holds nothing the other tests rely on, so every kind can be deleted;
    the counts of a deleted kind are 0 afterwards (the suggest job may refill the others).
    """
    result = runner.invoke(suggest_app, ["delete-query", "--yes", "--output", "json"])
    assert result.exit_code == 0, f"Delete query failed: {result.stdout}"
    assert json.loads(result.stdout).get("response", {}).get("status") == 0
    assert _word_counts(runner)["query_words_num"] == 0

    result = runner.invoke(suggest_app, ["delete-document", "--yes"])
    assert result.exit_code == 0, f"Delete document failed: {result.stdout}"
    assert "deleted successfully" in result.stdout
    assert _word_counts(runner)["document_words_num"] == 0

    result = runner.invoke(suggest_app, ["delete-all", "--yes"])
    assert result.exit_code == 0, f"Delete all failed: {result.stdout}"
    assert "deleted successfully" in result.stdout
    assert _word_counts(runner)["total_words_num"] == 0
