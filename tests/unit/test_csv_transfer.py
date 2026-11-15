"""
Unit tests for the CSV upload and download of the badword and elevateword commands.
"""
import json
from unittest.mock import Mock, patch

import httpx
import pytest
import yaml
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClient, FessAPIClientError
from fessctl.commands.badword import badword_app
from fessctl.commands.elevateword import elevateword_app
from fessctl.config.settings import Settings

# (name, app, resource type in the output, multipart field)
CASES = [
    ("badword", badword_app, "BadWord", "badWordFile"),
    ("elevateword", elevateword_app, "ElevateWord", "elevateWordFile"),
]
case = pytest.mark.parametrize("name,app,resource,field", CASES, ids=[c[0] for c in CASES])


def make_client(version: str) -> FessAPIClient:
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://localhost:8080"
    settings.access_token = "test-token"
    settings.fess_version = version
    return FessAPIClient(settings)


def ok_response():
    response = Mock()
    response.json.return_value = {"response": {"status": 0}}
    return response


class TestClient:
    @pytest.mark.parametrize("version", ["15.10.0", "15.9.0", "14.19.2"])
    @case
    def test_upload_posts_multipart_with_the_files_field(self, name, app, resource, field, version, tmp_path):
        path = tmp_path / "words.csv"
        path.write_bytes("Word\nあいう\n".encode("utf-8"))
        with patch("httpx.post", return_value=ok_response()) as post:
            result = getattr(make_client(version), f"upload_{name}")(str(path))
        assert result == {"response": {"status": 0}}
        assert post.call_args[0][0] == f"http://localhost:8080/api/admin/{name}/upload"
        assert post.call_args[1]["files"] == {
            field: ("words.csv", "Word\nあいう\n".encode("utf-8"), "application/octet-stream")}
        assert "Content-Type" not in post.call_args[1]["headers"]
        assert post.call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @pytest.mark.parametrize("version", ["15.6.1", "15.7.0", "15.8.0"])
    @case
    def test_upload_is_refused_where_the_server_cannot_receive_it(self, name, app, resource, field, version, tmp_path):
        path = tmp_path / "words.csv"
        path.write_bytes(b"Word\n")
        with patch("httpx.post") as post, patch("httpx.put") as put:
            result = getattr(make_client(version), f"upload_{name}")(str(path))
        assert result["response"]["status"] == 1
        assert "15.9" in result["response"]["message"]
        post.assert_not_called()
        put.assert_not_called()

    @case
    def test_download_returns_the_content(self, name, app, resource, field):
        response = Mock(status_code=200, content=b'"Word"\n', headers={"content-type": "application/octet-stream"})
        with patch("httpx.get", return_value=response) as get:
            content = getattr(make_client("15.9.0"), f"download_{name}")()
        assert content == b'"Word"\n'
        assert get.call_args[0][0] == f"http://localhost:8080/api/admin/{name}/download"
        assert get.call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @case
    def test_download_error_raises_with_the_message(self, name, app, resource, field):
        response = Mock(status_code=400, headers={"content-type": "application/json;charset=UTF-8"})
        response.json.return_value = {"response": {"status": 1, "message": "Failed to download."}}
        with patch("httpx.get", return_value=response):
            with pytest.raises(FessAPIClientError) as error:
                getattr(make_client("15.9.0"), f"download_{name}")()
        assert error.value.content == "Failed to download."

    @case
    def test_download_network_error_raises(self, name, app, resource, field):
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(FessAPIClientError) as error:
                getattr(make_client("15.9.0"), f"download_{name}")()
        assert error.value.status_code == -1


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patched(request):
    """Patches FessAPIClient in the module of the command under test; yields the mock client."""
    name = request.node.callspec.params["name"]
    with patch(f"fessctl.commands.{name}.FessAPIClient") as client_class:
        yield client_class.return_value


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "words.csv"
    path.write_text("Word\nfoo\n")
    return path


@case
class TestUpload:
    def test_confirms_then_uploads(self, name, app, resource, field, patched, runner, csv_file):
        upload = getattr(patched, f"upload_{name}")
        upload.return_value = {"response": {"status": 0}}

        declined = runner.invoke(app, ["upload", str(csv_file)], input="n\n")
        assert declined.exit_code != 0
        upload.assert_not_called()

        result = runner.invoke(app, ["upload", str(csv_file)], input="y\n")
        assert result.exit_code == 0
        upload.assert_called_once_with(str(csv_file))
        # the import runs in the background, so success only means that Fess accepted the file
        assert "accepted" in result.stdout
        assert "imported successfully" not in result.stdout

    def test_prompt_says_the_import_merges(self, name, app, resource, field, patched, runner, csv_file):
        result = runner.invoke(app, ["upload", str(csv_file)], input="n\n")
        assert "Existing words are kept" in result.stdout
        assert "Replace" not in result.stdout

    def test_yes_skips_the_prompt(self, name, app, resource, field, patched, runner, csv_file):
        getattr(patched, f"upload_{name}").return_value = {"response": {"status": 0}}
        result = runner.invoke(app, ["upload", str(csv_file), "--yes"])
        assert result.exit_code == 0
        assert "Confirm" not in result.stdout and "?" not in result.stdout

    def test_missing_file(self, name, app, resource, field, patched, runner, tmp_path):
        result = runner.invoke(app, ["upload", str(tmp_path / "nope.csv"), "-y"])
        assert result.exit_code == 1
        assert "not found" in result.stdout
        getattr(patched, f"upload_{name}").assert_not_called()

    @pytest.mark.parametrize("output", ["json", "yaml"])
    def test_missing_file_is_reported_in_the_requested_format(
            self, name, app, resource, field, patched, runner, tmp_path, output):
        result = runner.invoke(app, ["upload", str(tmp_path / "nope.csv"), "-y", "-o", output])
        assert result.exit_code == 1
        parsed = json.loads(result.stdout) if output == "json" else yaml.safe_load(result.stdout)
        assert parsed["response"]["status"] == 1
        assert "not found" in parsed["response"]["message"]

    def test_directory_is_not_a_file(self, name, app, resource, field, patched, runner, tmp_path):
        result = runner.invoke(app, ["upload", str(tmp_path), "-y"])
        assert result.exit_code == 1
        getattr(patched, f"upload_{name}").assert_not_called()

    @pytest.mark.parametrize("output", ["text", "json", "yaml"])
    def test_failure_exits_with_status_in_every_format(
            self, name, app, resource, field, patched, runner, csv_file, output):
        getattr(patched, f"upload_{name}").return_value = {"response": {"status": 1, "message": "no upload here"}}
        result = runner.invoke(app, ["upload", str(csv_file), "-y", "-o", output])
        assert result.exit_code == 1
        assert "no upload here" in result.stdout

    def test_json_and_yaml_print_the_raw_response(self, name, app, resource, field, patched, runner, csv_file):
        getattr(patched, f"upload_{name}").return_value = {"response": {"status": 0}}
        as_json = runner.invoke(app, ["upload", str(csv_file), "-y", "-o", "json"])
        assert json.loads(as_json.stdout) == {"response": {"status": 0}}
        as_yaml = runner.invoke(app, ["upload", str(csv_file), "-y", "-o", "yaml"])
        assert yaml.safe_load(as_yaml.stdout) == {"response": {"status": 0}}

    def test_text_failure_names_the_resource(self, name, app, resource, field, patched, runner, csv_file):
        getattr(patched, f"upload_{name}").return_value = {"response": {"status": 1, "message": "boom"}}
        result = runner.invoke(app, ["upload", str(csv_file), "-y"])
        assert f"Failed to upload {resource}." in result.stdout
        assert "Status code: 1" in result.stdout


@case
class TestDownload:
    def test_to_standard_output(self, name, app, resource, field, patched, runner):
        getattr(patched, f"download_{name}").return_value = "\"Word\"\nあいう\n".encode("utf-8")
        result = runner.invoke(app, ["download"])
        assert result.exit_code == 0
        assert result.stdout_bytes == "\"Word\"\nあいう\n".encode("utf-8")

    def test_to_file_refuses_to_overwrite_without_force(self, name, app, resource, field, patched, runner, tmp_path):
        download = getattr(patched, f"download_{name}")
        path = tmp_path / "out.csv"

        download.return_value = b"new"
        result = runner.invoke(app, ["download", "--file", str(path)])
        assert result.exit_code == 0
        assert path.read_bytes() == b"new"

        download.return_value = b"newer"
        result = runner.invoke(app, ["download", "--file", str(path)])
        assert result.exit_code == 1
        assert "already exists" in result.stdout
        assert path.read_bytes() == b"new"

        result = runner.invoke(app, ["download", "--file", str(path), "--force"])
        assert result.exit_code == 0
        assert path.read_bytes() == b"newer"

    @pytest.mark.parametrize("output", ["json", "yaml"])
    def test_existing_file_is_refused_in_the_requested_format_before_downloading(
            self, name, app, resource, field, patched, runner, tmp_path, output):
        path = tmp_path / "out.csv"
        path.write_bytes(b"old")
        result = runner.invoke(app, ["download", "--file", str(path), "-o", output])
        assert result.exit_code == 1
        parsed = json.loads(result.stdout) if output == "json" else yaml.safe_load(result.stdout)
        assert parsed["response"]["status"] == 1
        assert "already exists" in parsed["response"]["message"]
        getattr(patched, f"download_{name}").assert_not_called()
        assert path.read_bytes() == b"old"

    def test_to_file_reports_path_and_size(self, name, app, resource, field, patched, runner, tmp_path):
        getattr(patched, f"download_{name}").return_value = b"abc"
        path = tmp_path / "out.csv"
        result = runner.invoke(app, ["download", "-f", str(path), "-o", "json"])
        assert json.loads(result.stdout) == {"response": {"status": 0, "path": str(path), "size": 3}}

    @pytest.mark.parametrize("output", ["text", "json", "yaml"])
    def test_failure_exits_non_zero_in_every_format(
            self, name, app, resource, field, patched, runner, tmp_path, output):
        getattr(patched, f"download_{name}").side_effect = FessAPIClientError(400, "Failed to download.")
        path = tmp_path / "out.csv"
        result = runner.invoke(app, ["download", "--file", str(path), "-o", output])
        assert result.exit_code == 1
        assert "Failed to download." in result.stdout
        assert not path.exists()

    def test_failure_to_standard_output_writes_no_csv(self, name, app, resource, field, patched, runner):
        getattr(patched, f"download_{name}").side_effect = FessAPIClientError(403, "Forbidden")
        result = runner.invoke(app, ["download"])
        assert result.exit_code == 1
        assert f"Failed to download {resource}." in result.stdout
