"""
Unit tests for the suggest command.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.suggest import suggest_app


@pytest.fixture
def runner():
    return CliRunner()


class TestSuggestInfo:
    @patch("fessctl.commands.suggest.FessAPIClient")
    def test_info_text_output(self, mock_client_class, runner):
        mock_client_class.return_value.get_suggest_info.return_value = {"response": {"status": 0, "setting": {
            "total_words_num": 7, "document_words_num": 5, "query_words_num": 2}}}

        result = runner.invoke(suggest_app, ["info"])

        assert result.exit_code == 0
        assert "| total_words_num | 7 |" in result.stdout
        assert "| document_words_num | 5 |" in result.stdout
        assert "| query_words_num | 2 |" in result.stdout

    @patch("fessctl.commands.suggest.FessAPIClient")
    def test_info_failure_exits_with_status(self, mock_client_class, runner):
        mock_client_class.return_value.get_suggest_info.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}

        result = runner.invoke(suggest_app, ["info"])

        assert result.exit_code == 3
        assert "Unauthorized request." in result.stdout


DELETES = [
    ("delete-all", "delete_all_suggest_words", "All suggest words deleted"),
    ("delete-document", "delete_document_suggest_words", "Suggest words from documents deleted"),
    ("delete-query", "delete_query_suggest_words", "Suggest words from search queries deleted"),
]


class TestSuggestDelete:
    @pytest.mark.parametrize("command,method,message", DELETES)
    @patch("fessctl.commands.suggest.FessAPIClient")
    def test_delete_aborts_without_confirmation(self, mock_client_class, command, method, message, runner):
        result = runner.invoke(suggest_app, [command], input="n\n")

        assert result.exit_code != 0
        getattr(mock_client_class.return_value, method).assert_not_called()

    @pytest.mark.parametrize("command,method,message", DELETES)
    @patch("fessctl.commands.suggest.FessAPIClient")
    def test_delete_with_yes(self, mock_client_class, command, method, message, runner):
        mock_client = Mock()
        getattr(mock_client, method).return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(suggest_app, [command, "--yes"])

        assert result.exit_code == 0
        assert message in result.stdout
        getattr(mock_client, method).assert_called_once_with()

    @pytest.mark.parametrize("command,method,message", DELETES)
    @patch("fessctl.commands.suggest.FessAPIClient")
    def test_delete_confirmed_at_the_prompt(self, mock_client_class, command, method, message, runner):
        mock_client = Mock()
        getattr(mock_client, method).return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(suggest_app, [command], input="y\n")

        assert result.exit_code == 0
        getattr(mock_client, method).assert_called_once_with()

    @pytest.mark.parametrize("command,method,message", DELETES)
    @patch("fessctl.commands.suggest.FessAPIClient")
    def test_delete_failure_exits_with_status(self, mock_client_class, command, method, message, runner):
        mock_client = Mock()
        getattr(mock_client, method).return_value = {"response": {"status": 1, "message": "Failed to delete."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(suggest_app, [command, "-y", "-o", "json"])

        assert result.exit_code == 1
