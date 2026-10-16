"""
Unit tests for the failureurl command.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.failureurl import failureurl_app


@pytest.fixture
def runner():
    return CliRunner()


class TestFailureUrlList:
    @patch("fessctl.commands.failureurl.FessAPIClient")
    def test_list_sends_only_given_filters(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.list_failureurls.return_value = {"response": {"status": 0, "logs": []}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            failureurl_app,
            ["list", "--error-count-min", "2", "--url", "http://example.com/"],
        )

        assert result.exit_code == 0
        assert "No FailureUrls found." in result.stdout
        mock_client.list_failureurls.assert_called_once_with(
            page=1, size=100,
            filters={"url": "http://example.com/", "error_count_min": 2},
        )

    @patch("fessctl.commands.failureurl.FessAPIClient")
    def test_list_without_filters_sends_none(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.list_failureurls.return_value = {"response": {"status": 0, "logs": []}}
        mock_client_class.return_value = mock_client

        runner.invoke(failureurl_app, ["list"])

        mock_client.list_failureurls.assert_called_once_with(page=1, size=100, filters={})

    @patch("fessctl.commands.failureurl.FessAPIClient")
    def test_list_text_output(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.list_failureurls.return_value = {"response": {"status": 0, "logs": [
            {"id": "fu1", "url": "http://example.com/a", "error_name": "ConnectException",
             "error_count": 3, "last_access_time": 1792149753263},
        ]}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(failureurl_app, ["list"])

        assert result.exit_code == 0
        assert "| fu1 | http://example.com/a | ConnectException | 3 | 2026-10-16T11:22:33Z |" in result.stdout

    @patch("fessctl.commands.failureurl.FessAPIClient")
    def test_list_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.list_failureurls.return_value = {"response": {"status": 1, "message": "boom"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(failureurl_app, ["list"])

        assert result.exit_code == 1
        assert "boom" in result.stdout


class TestFailureUrlDeleteAll:
    @patch("fessctl.commands.failureurl.FessAPIClient")
    def test_delete_all_aborts_without_confirmation(self, mock_client_class, runner):
        result = runner.invoke(failureurl_app, ["delete-all"], input="n\n")

        assert result.exit_code != 0
        mock_client_class.return_value.delete_all_failureurls.assert_not_called()

    @patch("fessctl.commands.failureurl.FessAPIClient")
    def test_delete_all_with_yes(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.delete_all_failureurls.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(failureurl_app, ["delete-all", "--yes"])

        assert result.exit_code == 0
        assert "All FailureUrls deleted successfully." in result.stdout
        mock_client.delete_all_failureurls.assert_called_once_with()
