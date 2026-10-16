"""
Unit tests for the searchlist command and its client methods.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClient
from fessctl.commands.searchlist import searchlist_app
from fessctl.config.settings import Settings


@pytest.fixture
def runner():
    return CliRunner()


def _client(version):
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://fess"
    settings.access_token = "token"
    settings.fess_version = version
    return FessAPIClient(settings)


@pytest.fixture
def http():
    response = Mock()
    response.json.return_value = {"response": {"status": 0}}
    with patch("httpx.get", return_value=response) as get, \
            patch("httpx.post", return_value=response) as post, \
            patch("httpx.put", return_value=response) as put, \
            patch("httpx.delete", return_value=response) as delete, \
            patch("httpx.request", return_value=response) as request:
        yield Mock(get=get, post=post, put=put, delete=delete, request=request)


class TestSearchlistClient:
    def test_search_sends_only_given_params_in_body_and_query(self, http):
        _client("15.9.0").search_documents(query="foo", start=20, size=10, lang=["ja"])

        assert http.request.call_args[0] == ("GET", "http://fess/api/admin/searchlist/docs")
        expected = {"q": "foo", "start": 20, "size": 10, "lang": ["ja"]}
        assert http.request.call_args[1]["json"] == expected
        assert http.request.call_args[1]["params"] == expected

    def test_search_without_arguments_sends_empty_params(self, http):
        _client("15.9.0").search_documents()

        assert http.request.call_args[1]["json"] == {}

    def test_get_and_delete_use_doc_id_path(self, http):
        client = _client("15.9.0")

        client.get_document("abc")
        client.delete_document("abc")

        assert http.get.call_args[0][0] == "http://fess/api/admin/searchlist/doc/abc"
        assert http.delete.call_args[0][0] == "http://fess/api/admin/searchlist/doc/abc"

    def test_delete_by_query_sends_query_in_body(self, http):
        _client("15.9.0").delete_documents_by_query("foo")

        assert http.request.call_args[0] == ("DELETE", "http://fess/api/admin/searchlist/query")
        assert http.request.call_args[1]["json"] == {"q": "foo"}
        http.delete.assert_not_called()

    def test_create_posts_and_update_puts_on_fess15(self, http):
        client = _client("15.9.0")

        client.create_document({"url": "u"})
        client.update_document({"doc_id": "d"})

        assert http.post.call_args[0][0] == "http://fess/api/admin/searchlist/doc"
        assert http.post.call_args[1]["json"] == {"doc": {"url": "u"}}
        assert http.put.call_args[0][0] == "http://fess/api/admin/searchlist/doc"
        assert http.put.call_args[1]["json"] == {"doc": {"doc_id": "d"}}

    def test_create_puts_and_update_posts_on_fess14(self, http):
        client = _client("14.19.2")

        client.create_document({"url": "u"})
        client.update_document({"doc_id": "d"})

        assert http.put.call_args[1]["json"] == {"doc": {"url": "u"}}
        assert http.post.call_args[1]["json"] == {"doc": {"doc_id": "d"}}

    def test_bulk_puts_on_fess15_and_posts_on_fess14(self, http):
        _client("15.9.0").bulk_index_documents([{"url": "u"}])
        assert http.put.call_args[0][0] == "http://fess/api/admin/documents/bulk"
        assert http.put.call_args[1]["json"] == {"documents": [{"url": "u"}]}

        _client("14.19.2").bulk_index_documents([{"url": "u"}])
        assert http.post.call_args[0][0] == "http://fess/api/admin/documents/bulk"


class TestSearchlistSearch:
    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_search_passes_options(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.search_documents.return_value = {"response": {"status": 0, "docs": []}}

        result = runner.invoke(
            searchlist_app,
            ["search", "foo", "--start", "10", "--size", "5", "--sort", "last_modified.desc", "--lang", "ja"],
        )

        assert result.exit_code == 0
        assert "No documents found." in result.stdout
        mock_client.search_documents.assert_called_once_with(
            query="foo", start=10, size=5, sort="last_modified.desc", lang=["ja"])

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_search_without_options_sends_nothing(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.search_documents.return_value = {"response": {"status": 0, "docs": []}}

        runner.invoke(searchlist_app, ["search"])

        mock_client.search_documents.assert_called_once_with(
            query=None, start=None, size=None, sort=None, lang=None)

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_search_text_output(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.search_documents.return_value = {"response": {
            "status": 0, "record_count": 42, "start_record_number": 1, "end_record_number": 1,
            "docs": [{"doc_id": "d1", "title": "T", "url": "http://e/a", "last_modified": "2026-10-16T00:00:00.000Z"}],
        }}

        result = runner.invoke(searchlist_app, ["search", "foo"])

        assert result.exit_code == 0
        assert "## Documents (1-1 of 42)" in result.stdout
        assert "| d1 | T | http://e/a | 2026-10-16T00:00:00.000Z |" in result.stdout

    @patch("fessctl.commands.searchlist.FessAPIClient")
    @pytest.mark.parametrize("output", ["text", "json", "yaml"])
    def test_search_failure_exits_with_status(self, mock_client_class, runner, output):
        mock_client = mock_client_class.return_value
        mock_client.search_documents.return_value = {"response": {"status": 1, "message": "boom"}}

        result = runner.invoke(searchlist_app, ["search", "foo", "--output", output])

        assert result.exit_code == 1
        assert "boom" in result.stdout


class TestSearchlistGet:
    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_get_text_output(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.get_document.return_value = {"response": {"status": 0, "doc": {
            "doc_id": "d1", "url": "http://e/a", "title": "T", "role": ["Rguest", "1guest"], "boost": 1.0,
            "content": "x" * 300,
        }}}

        result = runner.invoke(searchlist_app, ["get", "d1"])

        assert result.exit_code == 0
        assert "| role | Rguest, 1guest |" in result.stdout
        assert "x" * 200 + "..." in result.stdout
        assert "x" * 201 not in result.stdout

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_get_not_found(self, mock_client_class, runner):
        mock_client_class.return_value.get_document.return_value = {
            "response": {"status": 1, "message": "The data nope is not found."}}

        result = runner.invoke(searchlist_app, ["get", "nope"])

        assert result.exit_code == 1
        assert "not found" in result.stdout


class TestSearchlistCreate:
    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_create_sends_the_given_fields(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.create_document.return_value = {"response": {"status": 0, "id": "d1"}}

        result = runner.invoke(searchlist_app, [
            "create", "--url", "http://e/a", "--title", "T", "--role", "Rguest", "--role", "1guest",
            "--content", "body", "--boost", "2", "--label", "L1", "--field", "mimetype=text/plain",
            "--field", "a=b=c",
        ])

        assert result.exit_code == 0
        assert "Document 'd1' created successfully." in result.stdout
        mock_client.create_document.assert_called_once_with({
            "url": "http://e/a", "title": "T", "role": ["Rguest", "1guest"], "content": "body",
            "boost": 2.0, "label": ["L1"], "mimetype": "text/plain", "a": "b=c",
        })

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_create_rejects_malformed_field(self, mock_client_class, runner):
        result = runner.invoke(searchlist_app, [
            "create", "--url", "u", "--title", "T", "--role", "r", "--field", "novalue"])

        assert result.exit_code == 1
        assert "KEY=VALUE" in result.stdout
        mock_client_class.return_value.create_document.assert_not_called()

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_create_failure_exits_with_status(self, mock_client_class, runner):
        mock_client_class.return_value.create_document.return_value = {
            "response": {"status": 1, "message": "Validation Error"}}

        result = runner.invoke(searchlist_app, ["create", "--url", "u", "--title", "T", "--role", "r"])

        assert result.exit_code == 1
        assert "Validation Error" in result.stdout


class TestSearchlistUpdate:
    STORED = {"response": {"status": 0, "doc": {
        "doc_id": "d1", "url": "http://e/a", "title": "T", "role": ["Rguest"], "boost": 1.0,
        "content": "body", "label": ["L1"], "_id": "x", "_version": 3, "_seq_no": -2, "_primary_term": 0,
    }}}

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_update_sends_back_the_required_fields_with_the_change(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.get_document.return_value = self.STORED
        mock_client.update_document.return_value = {"response": {"status": 0, "id": "d1"}}

        result = runner.invoke(searchlist_app, ["update", "d1", "--title", "New", "--field", "click_count=7"])

        assert result.exit_code == 0
        assert "Document 'd1' updated successfully." in result.stdout
        mock_client.update_document.assert_called_once_with({
            "doc_id": "d1", "url": "http://e/a", "title": "New", "role": ["Rguest"], "boost": 1.0,
            "click_count": "7",
        })

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_update_replaces_role_and_label_lists(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.get_document.return_value = self.STORED
        mock_client.update_document.return_value = {"response": {"status": 0, "id": "d1"}}

        runner.invoke(searchlist_app, ["update", "d1", "--role", "A", "--role", "B", "--label", "L2"])

        sent = mock_client.update_document.call_args[0][0]
        assert sent["role"] == ["A", "B"]
        assert sent["label"] == ["L2"]

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_update_without_changes_does_not_call_the_api(self, mock_client_class, runner):
        result = runner.invoke(searchlist_app, ["update", "d1"])

        assert result.exit_code == 1
        assert "Nothing to update" in result.stdout
        mock_client_class.return_value.get_document.assert_not_called()

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_update_of_missing_document_fails_before_updating(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.get_document.return_value = {"response": {"status": 1, "message": "not found"}}

        result = runner.invoke(searchlist_app, ["update", "nope", "--title", "x"])

        assert result.exit_code == 1
        assert "not found" in result.stdout
        mock_client.update_document.assert_not_called()

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_update_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.get_document.return_value = self.STORED
        mock_client.update_document.return_value = {"response": {"status": 1, "message": "boom"}}

        result = runner.invoke(searchlist_app, ["update", "d1", "--title", "x"])

        assert result.exit_code == 1
        assert "boom" in result.stdout


class TestSearchlistDelete:
    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_delete_success(self, mock_client_class, runner):
        mock_client_class.return_value.delete_document.return_value = {"response": {"status": 0}}

        result = runner.invoke(searchlist_app, ["delete", "d1"])

        assert result.exit_code == 0
        assert "Document 'd1' deleted successfully." in result.stdout

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_delete_failure_exits_with_status(self, mock_client_class, runner):
        mock_client_class.return_value.delete_document.return_value = {
            "response": {"status": 1, "message": "not found"}}

        result = runner.invoke(searchlist_app, ["delete", "d1"])

        assert result.exit_code == 1


class TestSearchlistDeleteByQuery:
    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_aborts_without_confirmation(self, mock_client_class, runner):
        result = runner.invoke(searchlist_app, ["delete-by-query", "foo"], input="n\n")

        assert result.exit_code != 0
        mock_client_class.return_value.delete_documents_by_query.assert_not_called()

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_deletes_after_confirmation(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.delete_documents_by_query.return_value = {"response": {"status": 0, "count": 3}}

        result = runner.invoke(searchlist_app, ["delete-by-query", "foo"], input="y\n")

        assert result.exit_code == 0
        assert "3 document(s) deleted." in result.stdout
        mock_client.delete_documents_by_query.assert_called_once_with("foo")

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_yes_skips_confirmation(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.delete_documents_by_query.return_value = {"response": {"status": 0, "count": 0}}

        result = runner.invoke(searchlist_app, ["delete-by-query", "foo", "--yes"])

        assert result.exit_code == 0
        mock_client.delete_documents_by_query.assert_called_once_with("foo")

    @patch("fessctl.commands.searchlist.FessAPIClient")
    def test_failure_exits_with_status(self, mock_client_class, runner):
        mock_client_class.return_value.delete_documents_by_query.return_value = {
            "response": {"status": 1, "message": "unknown condition"}}

        result = runner.invoke(searchlist_app, ["delete-by-query", "foo", "--yes"])

        assert result.exit_code == 1
        assert "unknown condition" in result.stdout
