"""
Unit tests for the log command.
"""
import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClientError
from fessctl.commands.log import log_app

FILES = {"response": {"status": 0, "total": 2, "files": [
    {"name": "fess.log", "id": "ZmVzcy5sb2c=", "lastModified": "2026-10-16T12:23:38"},
    {"name": "audit.log", "id": "YXVkaXQubG9n", "lastModified": "2026-10-16T12:23:49"},
]}}


@pytest.fixture
def runner():
    return CliRunner()


class TestLogList:
    @patch("fessctl.commands.log.FessAPIClient")
    def test_list_text_output(self, mock_client_class, runner):
        mock_client_class.return_value.get_log_files.return_value = FILES

        result = runner.invoke(log_app, ["list"])

        assert result.exit_code == 0
        assert "| fess.log | ZmVzcy5sb2c= | 2026-10-16T12:23:38 |" in result.stdout

    @patch("fessctl.commands.log.FessAPIClient")
    def test_list_empty(self, mock_client_class, runner):
        mock_client_class.return_value.get_log_files.return_value = {"response": {"status": 0, "files": []}}

        result = runner.invoke(log_app, ["list"])

        assert result.exit_code == 0
        assert "No Log files found." in result.stdout

    @patch("fessctl.commands.log.FessAPIClient")
    def test_list_failure_exits_with_status(self, mock_client_class, runner):
        mock_client_class.return_value.get_log_files.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}

        result = runner.invoke(log_app, ["list"])

        assert result.exit_code == 3
        assert "Unauthorized request." in result.stdout


class TestLogDownload:
    @patch("fessctl.commands.log.FessAPIClient")
    def test_download_success(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.get_log_files.return_value = FILES
        mock_client.download_log_file.return_value = {"response": {"status": 0, "path": "x", "size": 12}}
        mock_client_class.return_value = mock_client
        dest = tmp_path / "fess.log"

        result = runner.invoke(log_app, ["download", "ZmVzcy5sb2c=", "--dest", str(dest)])

        assert result.exit_code == 0
        assert "downloaded" in result.stdout
        assert "(12 bytes)" in result.stdout
        mock_client.download_log_file.assert_called_once_with("ZmVzcy5sb2c=", dest)

    @patch("fessctl.commands.log.FessAPIClient")
    def test_download_unknown_id_is_not_requested(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.get_log_files.return_value = FILES
        mock_client_class.return_value = mock_client

        result = runner.invoke(log_app, ["download", "bm9wZS5sb2c=", "--dest", str(tmp_path / "x.log")])

        assert result.exit_code == 1
        assert "not found" in result.stdout
        mock_client.download_log_file.assert_not_called()

    @patch("fessctl.commands.log.FessAPIClient")
    def test_download_refuses_to_overwrite(self, mock_client_class, runner, tmp_path):
        dest = tmp_path / "fess.log"
        dest.write_text("keep")

        result = runner.invoke(log_app, ["download", "ZmVzcy5sb2c=", "--dest", str(dest)])

        assert result.exit_code == 1
        assert "--force" in result.stdout
        assert dest.read_text() == "keep"
        mock_client_class.return_value.download_log_file.assert_not_called()

    @patch("fessctl.commands.log.FessAPIClient")
    def test_download_force_overwrites(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.get_log_files.return_value = FILES
        mock_client.download_log_file.return_value = {"response": {"status": 0, "path": "x", "size": 1}}
        mock_client_class.return_value = mock_client
        dest = tmp_path / "fess.log"
        dest.write_text("old")

        result = runner.invoke(log_app, ["download", "ZmVzcy5sb2c=", "--dest", str(dest), "--force"])

        assert result.exit_code == 0
        mock_client.download_log_file.assert_called_once_with("ZmVzcy5sb2c=", dest)

    @patch("fessctl.commands.log.FessAPIClient")
    def test_download_server_error_exits_with_status(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.get_log_files.return_value = FILES
        mock_client.download_log_file.return_value = {"response": {"status": 1, "message": "Could not find x."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(log_app, ["download", "ZmVzcy5sb2c=", "-d", str(tmp_path / "x.log")])

        assert result.exit_code == 1
        assert "Could not find x." in result.stdout

    @patch("fessctl.commands.log.FessAPIClient")
    def test_download_client_error_json_output(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.get_log_files.side_effect = FessAPIClientError(-1, "Network error: refused")
        mock_client_class.return_value = mock_client

        result = runner.invoke(log_app, ["download", "ZmVzcy5sb2c=", "-d", str(tmp_path / "x.log"), "-o", "json"])

        assert result.exit_code == 1
        assert json.loads(result.stdout)["status"] == "error"
