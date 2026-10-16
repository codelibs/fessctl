"""
Unit tests for the dict command and its client methods.
"""
from unittest.mock import Mock, patch

import httpx
import pytest
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClient, FessAPIClientError
from fessctl.commands.dict import DICT_FIELDS, dict_app
from fessctl.config.settings import Settings

DICT_TYPES = sorted(DICT_FIELDS)


def make_client(version: str) -> FessAPIClient:
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://localhost:8080"
    settings.access_token = "test-token"
    settings.fess_version = version
    return FessAPIClient(settings)


def ok_response(body=None):
    response = Mock()
    response.json.return_value = body or {"response": {"status": 0}}
    return response


@pytest.fixture
def runner():
    return CliRunner()


class TestClient:
    def test_get_dicts(self):
        with patch("httpx.get", return_value=ok_response()) as get:
            make_client("15.9.0").get_dicts()
        assert get.call_args[0][0] == "http://localhost:8080/api/admin/dict"

    def test_list_dict_items_sends_paging_in_body_and_query(self):
        with patch("httpx.request", return_value=ok_response()) as request:
            make_client("15.9.0").list_dict_items("synonym", "ID1", page=2, size=1)
        assert request.call_args[0] == ("GET", "http://localhost:8080/api/admin/dict/synonym/settings/ID1")
        assert request.call_args[1]["json"] == {"page": 2, "size": 1}
        assert request.call_args[1]["params"] == {"page": 2, "size": 1}

    def test_get_dict_item(self):
        with patch("httpx.get", return_value=ok_response()) as get:
            make_client("15.9.0").get_dict_item("kuromoji", "ID1", 7)
        assert get.call_args[0][0] == "http://localhost:8080/api/admin/dict/kuromoji/setting/ID1/7"

    def test_delete_dict_item(self):
        with patch("httpx.delete", return_value=ok_response()) as delete:
            make_client("15.9.0").delete_dict_item("stopwords", "ID1", 7)
        assert delete.call_args[0][0] == "http://localhost:8080/api/admin/dict/stopwords/setting/ID1/7"

    @pytest.mark.parametrize("version,create,update", [
        ("15.9.0", "post", "put"),
        ("15.6.1", "post", "put"),
        ("14.19.2", "put", "post"),
    ])
    def test_create_and_update_methods_follow_the_fess_version(self, version, create, update):
        client = make_client(version)
        with patch(f"httpx.{create}", return_value=ok_response()) as created:
            client.create_dict_item("protwords", "ID1", {"input": "a"})
        assert created.call_args[0][0] == "http://localhost:8080/api/admin/dict/protwords/setting/ID1"
        assert created.call_args[1]["json"] == {"input": "a"}
        with patch(f"httpx.{update}", return_value=ok_response()) as updated:
            client.update_dict_item("protwords", "ID1", {"id": 1, "input": "b"})
        assert updated.call_args[1]["json"] == {"id": 1, "input": "b"}

    @pytest.mark.parametrize("version", ["15.9.0", "14.19.2"])
    @pytest.mark.parametrize("dict_type,field", [
        ("synonym", "synonymFile"), ("mapping", "charMappingFile"), ("kuromoji", "kuromojiFile"),
        ("stopwords", "stopwordsFile"), ("protwords", "protwordsFile"),
        ("stemmeroverride", "stemmerOverrideFile"),
    ])
    def test_upload_posts_multipart_with_the_types_field(self, version, dict_type, field, tmp_path):
        path = tmp_path / "words.txt"
        path.write_bytes(b"a\nb\n")
        with patch("httpx.post", return_value=ok_response()) as post:
            make_client(version).upload_dict(dict_type, "ID1", str(path))
        assert post.call_args[0][0] == f"http://localhost:8080/api/admin/dict/{dict_type}/upload/ID1"
        assert post.call_args[1]["files"] == {field: ("words.txt", b"a\nb\n", "application/octet-stream")}
        assert "Content-Type" not in post.call_args[1]["headers"]
        assert post.call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @pytest.mark.parametrize("version", ["15.6.1", "15.7.0", "15.8.0"])
    def test_upload_is_refused_where_the_server_cannot_receive_it(self, version, tmp_path):
        path = tmp_path / "words.txt"
        path.write_bytes(b"a\n")
        with patch("httpx.post") as post, patch("httpx.put") as put:
            result = make_client(version).upload_dict("synonym", "ID1", str(path))
        assert result["response"]["status"] == 1
        assert "15.9" in result["response"]["message"]
        post.assert_not_called()
        put.assert_not_called()

    def test_download_returns_the_content(self):
        response = Mock(status_code=200, content=b"a\nb\n", headers={"content-type": "application/octet-stream"})
        with patch("httpx.get", return_value=response) as get:
            content = make_client("15.9.0").download_dict("synonym", "ID1")
        assert content == b"a\nb\n"
        assert get.call_args[0][0] == "http://localhost:8080/api/admin/dict/synonym/download/ID1"

    def test_download_error_raises_with_the_message(self):
        response = Mock(status_code=400, headers={"content-type": "application/json;charset=UTF-8"})
        response.json.return_value = {"response": {"status": 1, "message": "Failed to download."}}
        with patch("httpx.get", return_value=response):
            with pytest.raises(FessAPIClientError) as error:
                make_client("15.9.0").download_dict("synonym", "nosuch")
        assert error.value.content == "Failed to download."

    def test_download_network_error_raises(self):
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(FessAPIClientError) as error:
                make_client("15.9.0").download_dict("synonym", "ID1")
        assert error.value.status_code == -1


def patched_client():
    """Patches FessAPIClient in the command module; returns (patcher, mock client)."""
    patcher = patch("fessctl.commands.dict.FessAPIClient")
    mock_client = Mock()
    patcher.start().return_value = mock_client
    return patcher, mock_client


@pytest.fixture
def client():
    patcher, mock_client = patched_client()
    yield mock_client
    patcher.stop()


class TestDictList:
    def test_list_text_output_and_type_filter(self, client, runner):
        client.get_dicts.return_value = {"response": {"status": 0, "settings": [
            {"id": "SY", "type": "synonym", "path": "synonym.txt", "timestamp": "2026-10-16T12:00:00"},
            {"id": "KU", "type": "kuromoji", "path": "ja/kuromoji.txt", "timestamp": "2026-10-16T12:00:01"},
        ]}}

        result = runner.invoke(dict_app, ["list"])
        assert result.exit_code == 0
        assert "| synonym | SY | synonym.txt | 2026-10-16T12:00:00 |" in result.stdout
        assert "| kuromoji | KU |" in result.stdout

        result = runner.invoke(dict_app, ["list", "--type", "kuromoji"])
        assert "| kuromoji | KU |" in result.stdout
        assert "synonym" not in result.stdout

        result = runner.invoke(dict_app, ["list", "--type", "mapping"])
        assert "No Dictionaries found." in result.stdout

    def test_list_failure_exits_with_status(self, client, runner):
        client.get_dicts.return_value = {"response": {"status": 1, "message": "boom"}}
        result = runner.invoke(dict_app, ["list"])
        assert result.exit_code == 1
        assert "boom" in result.stdout


# Command-line arguments that fill every field of each type, and the API body they must produce.
CREATE_CASES = {
    "synonym": (["--source", "a", "--source", "b", "--target", "c"], {"inputs": "a\nb", "outputs": "c"}),
    "mapping": (["--source", "a", "--source", "b", "--target", "c"], {"inputs": "a\nb", "output": "c"}),
    "kuromoji": (["--token", "t", "--segmentation", "s", "--reading", "r", "--pos", "p"],
                 {"token": "t", "segmentation": "s", "reading": "r", "pos": "p"}),
    "stopwords": (["--word", "w"], {"input": "w"}),
    "protwords": (["--word", "w"], {"input": "w"}),
    "stemmeroverride": (["--source", "a", "--target", "c"], {"input": "a", "output": "c"}),
}


class TestEntries:
    def test_every_type_has_a_create_case(self):
        assert sorted(CREATE_CASES) == DICT_TYPES

    @pytest.mark.parametrize("dict_type", DICT_TYPES)
    def test_create_sends_the_types_fields(self, client, runner, dict_type):
        args, body = CREATE_CASES[dict_type]
        client.create_dict_item.return_value = {"response": {"status": 0, "id": "7"}}

        result = runner.invoke(dict_app, [dict_type, "create", "ID1", *args])

        assert result.exit_code == 0, result.stdout
        assert "created successfully" in result.stdout
        client.create_dict_item.assert_called_once_with(dict_type, "ID1", body)

    def test_create_without_id_in_the_response_still_succeeds(self, client, runner):
        client.create_dict_item.return_value = {"response": {"status": 0, "id": "0"}}
        result = runner.invoke(dict_app, ["stopwords", "create", "ID1", "--word", "w"])
        assert result.exit_code == 0
        assert "stopwords entry created successfully." in result.stdout
        assert "'0'" not in result.stdout

    def test_create_requires_every_field(self, client, runner):
        result = runner.invoke(dict_app, ["mapping", "create", "ID1", "--source", "a"])
        assert result.exit_code == 2
        client.create_dict_item.assert_not_called()

    def test_create_failure_exits_with_status(self, client, runner):
        client.create_dict_item.return_value = {"response": {"status": 1, "message": "is invalid"}}
        result = runner.invoke(dict_app, ["synonym", "create", "ID1", "--source", "a,b", "--target", "c"])
        assert result.exit_code == 1
        assert "is invalid" in result.stdout

    def test_update_keeps_unspecified_fields(self, client, runner):
        client.get_dict_item.return_value = {"response": {"status": 0, "setting": {
            "id": 3, "dict_id": "ID1", "inputs": "a\nb", "outputs": "c"}}}
        client.update_dict_item.return_value = {"response": {"status": 0, "id": "3"}}

        result = runner.invoke(dict_app, ["synonym", "update", "ID1", "3", "--target", "x", "--target", "y"])

        assert result.exit_code == 0, result.stdout
        client.get_dict_item.assert_called_once_with("synonym", "ID1", 3)
        client.update_dict_item.assert_called_once_with(
            "synonym", "ID1", {"id": 3, "dict_id": "ID1", "inputs": "a\nb", "outputs": "x\ny"})

    def test_update_of_a_missing_entry_fails_without_writing(self, client, runner):
        client.get_dict_item.return_value = {"response": {"status": 1, "message": "gone"}}
        result = runner.invoke(dict_app, ["kuromoji", "update", "ID1", "3", "--pos", "p"])
        assert result.exit_code == 1
        assert "not found" in result.stdout
        client.update_dict_item.assert_not_called()

    def test_get_text_output(self, client, runner):
        client.get_dict_item.return_value = {"response": {"status": 0, "setting": {
            "id": 3, "dict_id": "ID1", "token": "t", "segmentation": "s", "reading": "r", "pos": "p"}}}
        result = runner.invoke(dict_app, ["kuromoji", "get", "ID1", "3"])
        assert result.exit_code == 0
        for row in ("| id | 3 |", "| token | t |", "| segmentation | s |", "| reading | r |", "| pos | p |"):
            assert row in result.stdout

    def test_get_failure_exits_with_status(self, client, runner):
        client.get_dict_item.return_value = {"response": {"status": 1, "message": "gone"}}
        result = runner.invoke(dict_app, ["synonym", "get", "ID1", "9"])
        assert result.exit_code == 1
        assert "Failed to retrieve synonym entry" in result.stdout

    def test_delete(self, client, runner):
        client.delete_dict_item.return_value = {"response": {"status": 0}}
        result = runner.invoke(dict_app, ["protwords", "delete", "ID1", "3"])
        assert result.exit_code == 0
        client.delete_dict_item.assert_called_once_with("protwords", "ID1", 3)

    def test_item_id_must_be_a_number(self, client, runner):
        result = runner.invoke(dict_app, ["protwords", "delete", "ID1", "abc"])
        assert result.exit_code == 2
        client.delete_dict_item.assert_not_called()

    def test_list_passes_paging_and_shows_the_fields(self, client, runner):
        client.list_dict_items.return_value = {"response": {"status": 0, "settings": [
            {"id": 1, "dict_id": "ID1", "inputs": "a\nb", "outputs": "c"}]}}
        result = runner.invoke(dict_app, ["synonym", "list", "ID1", "--page", "2", "--size", "5"])
        assert result.exit_code == 0
        client.list_dict_items.assert_called_once_with("synonym", "ID1", page=2, size=5)
        assert "| 1 | a<br>b | c |" in result.stdout

    def test_list_empty(self, client, runner):
        client.list_dict_items.return_value = {"response": {"status": 0, "settings": []}}
        result = runner.invoke(dict_app, ["mapping", "list", "ID1"])
        assert "No mapping entries found." in result.stdout

    def test_json_output_is_the_raw_response(self, client, runner):
        client.list_dict_items.return_value = {"response": {"status": 0, "settings": [], "total": 0}}
        result = runner.invoke(dict_app, ["mapping", "list", "ID1", "-o", "json"])
        assert '"total": 0' in result.stdout


class TestUpload:
    def test_upload_confirms_then_uploads(self, client, runner, tmp_path):
        path = tmp_path / "words.txt"
        path.write_text("a\n")
        client.upload_dict.return_value = {"response": {"status": 0}}

        declined = runner.invoke(dict_app, ["stopwords", "upload", "ID1", str(path)], input="n\n")
        assert declined.exit_code != 0
        client.upload_dict.assert_not_called()

        result = runner.invoke(dict_app, ["stopwords", "upload", "ID1", str(path)], input="y\n")
        assert result.exit_code == 0
        client.upload_dict.assert_called_once_with("stopwords", "ID1", str(path))

    def test_upload_yes_skips_the_prompt(self, client, runner, tmp_path):
        path = tmp_path / "words.txt"
        path.write_text("a\n")
        client.upload_dict.return_value = {"response": {"status": 0}}
        result = runner.invoke(dict_app, ["stopwords", "upload", "ID1", str(path), "--yes"])
        assert result.exit_code == 0
        assert "replaced successfully" in result.stdout

    def test_upload_missing_file(self, client, runner, tmp_path):
        result = runner.invoke(dict_app, ["stopwords", "upload", "ID1", str(tmp_path / "nope.txt"), "-y"])
        assert result.exit_code == 1
        assert "not found" in result.stdout
        client.upload_dict.assert_not_called()

    def test_upload_failure_exits_with_status(self, client, runner, tmp_path):
        path = tmp_path / "words.txt"
        path.write_text("a\n")
        client.upload_dict.return_value = {"response": {"status": 1, "message": "no upload here"}}
        result = runner.invoke(dict_app, ["stopwords", "upload", "ID1", str(path), "-y"])
        assert result.exit_code == 1
        assert "no upload here" in result.stdout


class TestDownload:
    def test_download_to_standard_output(self, client, runner):
        client.download_dict.return_value = b"a\nb\n"
        result = runner.invoke(dict_app, ["synonym", "download", "ID1"])
        assert result.exit_code == 0
        assert result.stdout_bytes == b"a\nb\n"

    def test_download_to_file_refuses_to_overwrite(self, client, runner, tmp_path):
        client.download_dict.return_value = b"new"
        path = tmp_path / "out.txt"

        result = runner.invoke(dict_app, ["synonym", "download", "ID1", "--file", str(path)])
        assert result.exit_code == 0
        assert path.read_bytes() == b"new"

        client.download_dict.return_value = b"newer"
        result = runner.invoke(dict_app, ["synonym", "download", "ID1", "--file", str(path)])
        assert result.exit_code == 1
        assert "already exists" in result.stdout
        assert path.read_bytes() == b"new"

        result = runner.invoke(dict_app, ["synonym", "download", "ID1", "--file", str(path), "--force"])
        assert result.exit_code == 0
        assert path.read_bytes() == b"newer"

    def test_download_failure_exits_non_zero(self, client, runner, tmp_path):
        client.download_dict.side_effect = FessAPIClientError(400, "Failed to download a protwords file.")
        path = tmp_path / "out.txt"
        result = runner.invoke(dict_app, ["synonym", "download", "nosuch", "--file", str(path)])
        assert result.exit_code == 1
        assert "Failed to download a protwords file." in result.stdout
        assert not path.exists()
