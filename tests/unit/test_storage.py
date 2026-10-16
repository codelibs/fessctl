"""
Unit tests for the storage command.
"""
import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.storage import storage_app


@pytest.fixture
def runner():
    return CliRunner()


def _download_response(body=b"hello", content_type="application/octet-stream", content_length=None, json_body=None):
    response = Mock()
    response.content = body
    response.headers = {"content-type": content_type}
    if content_length is not None:
        response.headers["content-length"] = content_length
    response.json.return_value = json_body
    return response


class TestStorageList:
    @patch("fessctl.commands.storage.FessAPIClient")
    def test_list_shows_full_object_paths(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_storage_items.return_value = {"response": {"status": 0, "items": [
            {"path": "docs", "name": "sub", "directory": True, "size": 0},
            {"path": "docs", "name": "a.txt", "directory": False, "size": 6, "lastModified": "2026-10-16T12:28:45Z"},
            {"name": "top.txt", "directory": False, "size": 6, "lastModified": "2026-10-16T12:28:46Z"},
        ]}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(storage_app, ["list", "docs"])

        assert result.exit_code == 0
        assert "| docs/sub | directory | 0 | - |" in result.stdout
        assert "| docs/a.txt | file | 6 | 2026-10-16T12:28:45Z |" in result.stdout
        assert "| top.txt | file | 6 | 2026-10-16T12:28:46Z |" in result.stdout
        mock_client.get_storage_items.assert_called_once_with("docs")

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_list_defaults_to_the_root(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_storage_items.return_value = {"response": {"status": 0, "items": []}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(storage_app, ["list"])

        assert "No Storage items found." in result.stdout
        mock_client.get_storage_items.assert_called_once_with("")

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_list_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_storage_items.return_value = {"response": {"status": 1, "message": "Storage Access Error: No storage client is registered"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(storage_app, ["list"])

        assert result.exit_code == 1
        assert "No storage client is registered" in result.stdout


class TestStorageListTimeout:
    @patch("fessctl.commands.storage.FessAPIClient")
    def test_list_waits_for_a_slow_backend(self, mock_client_class, runner):
        mock_client_class.return_value.get_storage_items.return_value = {"response": {"status": 0, "items": []}}

        runner.invoke(storage_app, ["list"])

        assert mock_client_class.call_args.kwargs["timeout"] >= 60


class TestStorageDownload:
    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_to_file(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_storage_file.return_value = _download_response(b"\x00\x01binary")
        mock_client_class.return_value = mock_client
        target = tmp_path / "out.bin"

        result = runner.invoke(storage_app, ["download", "docs/a.bin", "--file", str(target)])

        assert result.exit_code == 0
        assert target.read_bytes() == b"\x00\x01binary"
        mock_client.download_storage_file.assert_called_once_with("docs/a.bin")

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_refuses_a_missing_parent_directory(self, mock_client_class, runner, tmp_path):
        target = tmp_path / "missing" / "a.txt"

        result = runner.invoke(storage_app, ["download", "docs/a.txt", "--file", str(target)])

        assert result.exit_code == 1
        assert "does not exist" in result.stdout
        mock_client_class.return_value.download_storage_file.assert_not_called()

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_to_stdout(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.download_storage_file.return_value = _download_response(b"hello\n")
        mock_client_class.return_value = mock_client

        result = runner.invoke(storage_app, ["download", "top.txt"])

        assert result.exit_code == 0
        assert result.stdout_bytes == b"hello\n"

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_refuses_to_overwrite(self, mock_client_class, runner, tmp_path):
        target = tmp_path / "out.txt"
        target.write_text("keep")

        result = runner.invoke(storage_app, ["download", "top.txt", "--file", str(target)])

        assert result.exit_code == 1
        assert target.read_text() == "keep"
        mock_client_class.return_value.download_storage_file.assert_not_called()

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_force_overwrites(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_storage_file.return_value = _download_response(b"new")
        mock_client_class.return_value = mock_client
        target = tmp_path / "out.txt"
        target.write_text("old")

        result = runner.invoke(storage_app, ["download", "top.txt", "--file", str(target), "--force"])

        assert result.exit_code == 0
        assert target.read_text() == "new"

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_json_error_body_fails(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_storage_file.return_value = _download_response(
            content_type="application/json;charset=UTF-8",
            json_body={"response": {"status": 1, "message": "The file was not found."}})
        mock_client_class.return_value = mock_client
        target = tmp_path / "out.txt"

        result = runner.invoke(storage_app, ["download", "top.txt", "--file", str(target)])

        assert result.exit_code == 1
        assert "The file was not found." in result.stdout
        assert not target.exists()

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_explicit_empty_body_is_a_failure(self, mock_client_class, runner, tmp_path):
        # Fess answers 200 with Content-Length: 0 when it cannot read the object
        mock_client = Mock()
        mock_client.download_storage_file.return_value = _download_response(b"", content_length="0")
        mock_client_class.return_value = mock_client
        target = tmp_path / "out.txt"

        result = runner.invoke(storage_app, ["download", "missing.txt", "--file", str(target)])

        assert result.exit_code == 1
        assert "empty response" in result.stdout
        assert not target.exists()

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_empty_object_sent_chunked_is_written(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_storage_file.return_value = _download_response(b"")
        mock_client_class.return_value = mock_client
        target = tmp_path / "empty.txt"

        result = runner.invoke(storage_app, ["download", "empty.txt", "--file", str(target)])

        assert result.exit_code == 0
        assert target.read_bytes() == b""

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_download_json_output(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.download_storage_file.return_value = _download_response(b"abc")
        mock_client_class.return_value = mock_client
        target = tmp_path / "out.txt"

        result = runner.invoke(storage_app, ["download", "top.txt", "--file", str(target), "--output", "json"])

        assert json.loads(result.stdout) == {"response": {"status": 0, "file": str(target), "size": 3}}


class TestStorageUpload:
    @patch("fessctl.commands.storage.FessAPIClient")
    def test_upload(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.upload_storage_file.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client
        source = tmp_path / "report.pdf"
        source.write_bytes(b"pdf")

        result = runner.invoke(storage_app, ["upload", str(source), "--dir", "docs/2026"])

        assert result.exit_code == 0
        assert "'docs/2026/report.pdf'" in result.stdout
        mock_client.upload_storage_file.assert_called_once_with(source, "docs/2026")

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_upload_to_root(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.upload_storage_file.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client
        source = tmp_path / "report.pdf"
        source.write_bytes(b"pdf")

        result = runner.invoke(storage_app, ["upload", str(source)])

        assert "'report.pdf'" in result.stdout
        mock_client.upload_storage_file.assert_called_once_with(source, "")

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_upload_failure_exits_with_status(self, mock_client_class, runner, tmp_path):
        mock_client = Mock()
        mock_client.upload_storage_file.return_value = {"response": {"status": 1, "message": "Failed to upload report.pdf."}}
        mock_client_class.return_value = mock_client
        source = tmp_path / "report.pdf"
        source.write_bytes(b"pdf")

        result = runner.invoke(storage_app, ["upload", str(source)])

        assert result.exit_code == 1
        assert "Failed to upload report.pdf." in result.stdout

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_upload_missing_file(self, mock_client_class, runner, tmp_path):
        result = runner.invoke(storage_app, ["upload", str(tmp_path / "missing.bin")])

        assert result.exit_code == 2
        mock_client_class.return_value.upload_storage_file.assert_not_called()


class TestStorageDelete:
    @patch("fessctl.commands.storage.FessAPIClient")
    def test_delete_aborts_without_confirmation(self, mock_client_class, runner):
        result = runner.invoke(storage_app, ["delete", "docs/a.txt"], input="n\n")

        assert result.exit_code != 0
        mock_client_class.return_value.delete_storage_file.assert_not_called()

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_delete_with_yes(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.delete_storage_file.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(storage_app, ["delete", "docs/a.txt", "--yes"])

        assert result.exit_code == 0
        assert "deleted successfully" in result.stdout
        mock_client.delete_storage_file.assert_called_once_with("docs/a.txt")

    @patch("fessctl.commands.storage.FessAPIClient")
    def test_delete_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.delete_storage_file.return_value = {"response": {"status": 1, "message": "Failed to delete the file a.txt."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(storage_app, ["delete", "a.txt", "--yes"])

        assert result.exit_code == 1
        assert "Failed to delete the file a.txt." in result.stdout


@pytest.mark.parametrize("output", ["json", "yaml"])
@patch("fessctl.commands.storage.FessAPIClient")
def test_failure_exits_with_status_in_every_format(mock_client_class, output, tmp_path):
    mock_client = Mock()
    failure = {"response": {"status": 1, "message": "Storage Access Error"}}
    mock_client.get_storage_items.return_value = failure
    mock_client.delete_storage_file.return_value = failure
    mock_client_class.return_value = mock_client
    runner = CliRunner()

    assert runner.invoke(storage_app, ["list", "--output", output]).exit_code == 1
    assert runner.invoke(storage_app, ["delete", "a.txt", "--yes", "--output", output]).exit_code == 1
