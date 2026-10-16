"""
Unit tests for the general command.
"""
import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.general import general_app

SETTING = {
    "day_for_cleanup": 3,
    "crawling_thread_count": 5,
    "failure_count_threshold": -1,
    "csv_file_encoding": "UTF-8",
    "purge_job_log_day": -1,
    "notification_login": "",
    "storage_secret_key": "**********",
}


@pytest.fixture
def runner():
    return CliRunner()


def _client(mock_client_class, update_status=0):
    mock_client = Mock()
    mock_client.get_general.return_value = {"response": {"status": 0, "setting": dict(SETTING)}}
    mock_client.update_general.return_value = {"response": {"status": update_status}}
    mock_client_class.return_value = mock_client
    return mock_client


class TestGeneralGet:
    @patch("fessctl.commands.general.FessAPIClient")
    def test_get_text_output(self, mock_client_class, runner):
        _client(mock_client_class)

        result = runner.invoke(general_app, ["get"])

        assert result.exit_code == 0
        assert "| day_for_cleanup | 3 |" in result.stdout
        assert "| storage_secret_key | ********** |" in result.stdout

    @patch("fessctl.commands.general.FessAPIClient")
    def test_get_json_output(self, mock_client_class, runner):
        _client(mock_client_class)

        result = runner.invoke(general_app, ["get", "--output", "json"])

        assert json.loads(result.stdout)["response"]["setting"]["csv_file_encoding"] == "UTF-8"

    @patch("fessctl.commands.general.FessAPIClient")
    def test_get_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_general.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(general_app, ["get"])

        assert result.exit_code == 3
        assert "Unauthorized request." in result.stdout


class TestGeneralUpdate:
    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_sends_required_keys_and_only_the_changes(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)

        result = runner.invoke(general_app, ["update", "--set", "notification_login=hello", "--set", "purge_job_log_day=45"])

        assert result.exit_code == 0
        assert "General settings updated (notification_login, purge_job_log_day)." in result.stdout
        mock_client.update_general.assert_called_once_with({
            "day_for_cleanup": 3,
            "crawling_thread_count": 5,
            "failure_count_threshold": -1,
            "csv_file_encoding": "UTF-8",
            "notification_login": "hello",
            "purge_job_log_day": 45,
        })

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_never_echoes_masked_secrets(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)

        runner.invoke(general_app, ["update", "--set", "notification_login=x"])

        assert "storage_secret_key" not in mock_client.update_general.call_args[0][0]

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_value_may_contain_equals_and_be_empty(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)

        runner.invoke(general_app, ["update", "--set", "csv_file_encoding=a=b", "--set", "notification_login="])

        sent = mock_client.update_general.call_args[0][0]
        assert sent["csv_file_encoding"] == "a=b"
        assert sent["notification_login"] == ""

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_accepts_settings_the_server_omits_while_unset(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)

        result = runner.invoke(general_app, ["update", "--set", "ldap_provider_url=ldap://localhost:389"])

        assert result.exit_code == 0
        assert mock_client.update_general.call_args[0][0]["ldap_provider_url"] == "ldap://localhost:389"

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_rejects_unknown_setting(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)

        result = runner.invoke(general_app, ["update", "--set", "no_such_setting=1"])

        assert result.exit_code == 2
        mock_client.update_general.assert_not_called()

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_rejects_non_integer_for_integer_setting(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)

        result = runner.invoke(general_app, ["update", "--set", "day_for_cleanup=abc"])

        assert result.exit_code == 2
        mock_client.update_general.assert_not_called()

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_requires_a_change(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)

        assert runner.invoke(general_app, ["update"]).exit_code == 2
        assert runner.invoke(general_app, ["update", "--set", "notification_login"]).exit_code == 2
        mock_client.update_general.assert_not_called()

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = _client(mock_client_class)
        mock_client.update_general.return_value = {"response": {"status": 1, "message": "must be less than or equal to 1000."}}

        result = runner.invoke(general_app, ["update", "--set", "day_for_cleanup=99999"])

        assert result.exit_code == 1
        assert "must be less than or equal to 1000." in result.stdout

    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_stops_when_get_fails(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_general.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(general_app, ["update", "--set", "notification_login=x"])

        assert result.exit_code == 3
        mock_client.update_general.assert_not_called()


class TestExitStatusInEveryFormat:
    @pytest.mark.parametrize("output", ["json", "yaml"])
    @patch("fessctl.commands.general.FessAPIClient")
    def test_get_failure_exits_with_status(self, mock_client_class, runner, output):
        mock_client = Mock()
        mock_client.get_general.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(general_app, ["get", "--output", output])

        assert result.exit_code == 3
        assert "Unauthorized request." in result.stdout

    @pytest.mark.parametrize("output", ["json", "yaml"])
    @patch("fessctl.commands.general.FessAPIClient")
    def test_update_failure_exits_with_status(self, mock_client_class, runner, output):
        mock_client = _client(mock_client_class)
        mock_client.update_general.return_value = {"response": {"status": 1, "message": "bad value"}}

        result = runner.invoke(general_app, ["update", "--set", "notification_login=x", "--output", output])

        assert result.exit_code == 1
