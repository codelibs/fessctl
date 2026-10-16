"""
Unit tests for the backup command.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.backup import backup_app


@pytest.fixture
def runner():
    return CliRunner()


class TestBackupList:
    @patch("fessctl.commands.backup.FessAPIClient")
    def test_list_text_output(self, mock_client_class, runner):
        mock_client_class.return_value.get_backup_files.return_value = {"response": {"status": 0, "total": 1, "files": [
            {"name": "fess_config.bulk", "id": "fess_config.bulk"},
        ]}}

        result = runner.invoke(backup_app, ["list"])

        assert result.exit_code == 0
        assert "| fess_config.bulk | fess_config.bulk |" in result.stdout

    @patch("fessctl.commands.backup.FessAPIClient")
    def test_list_failure_exits_with_status(self, mock_client_class, runner):
        mock_client_class.return_value.get_backup_files.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}

        result = runner.invoke(backup_app, ["list"])

        assert result.exit_code == 3
        assert "Unauthorized request." in result.stdout


class TestBackupDownload:
    @patch("fessctl.commands.backup.FessAPIClient")
    def test_download_success(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_backup_file.return_value = {"response": {"status": 0, "path": "x", "size": 0}}
        mock_client_class.return_value = mock_client
        dest = tmp_path / "search_log.ndjson"

        result = runner.invoke(backup_app, ["download", "search_log.ndjson", "--dest", str(dest)])

        assert result.exit_code == 0
        assert "(0 bytes)" in result.stdout
        mock_client.download_backup_file.assert_called_once_with("search_log.ndjson", dest)

    @patch("fessctl.commands.backup.FessAPIClient")
    def test_download_unknown_id_exits_with_status(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_backup_file.return_value = {"response": {"status": 1, "message": "Could not find any backup index."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(backup_app, ["download", "nope", "-d", str(tmp_path / "nope")])

        assert result.exit_code == 1
        assert "Could not find any backup index." in result.stdout

    @patch("fessctl.commands.backup.FessAPIClient")
    def test_download_refuses_to_overwrite(self, mock_client_class, runner, tmp_path):
        dest = tmp_path / "fess.json"
        dest.write_text("keep")

        result = runner.invoke(backup_app, ["download", "fess.json", "--dest", str(dest)])

        assert result.exit_code == 1
        assert "--force" in result.stdout
        assert dest.read_text() == "keep"
        mock_client_class.return_value.download_backup_file.assert_not_called()

    @patch("fessctl.commands.backup.FessAPIClient")
    def test_download_force_overwrites(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_backup_file.return_value = {"response": {"status": 0, "path": "x", "size": 3}}
        mock_client_class.return_value = mock_client
        dest = tmp_path / "fess.json"
        dest.write_text("old")

        result = runner.invoke(backup_app, ["download", "fess.json", "--dest", str(dest), "-f"])

        assert result.exit_code == 0
        mock_client.download_backup_file.assert_called_once_with("fess.json", dest)
