"""
Unit tests for the documents command. documents has a single subcommand, so a
bare Typer app collapses into it; invoke it through the real CLI instead.
"""
import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from fessctl.cli import app


@pytest.fixture
def runner():
    return CliRunner()


DOC1 = {"url": "http://e/1", "title": "one"}
DOC2 = {"url": "http://e/2", "title": "two"}


class TestDocumentsBulk:
    @pytest.mark.parametrize("text", [
        json.dumps([DOC1, DOC2]),
        json.dumps({"documents": [DOC1, DOC2]}),
        json.dumps(DOC1) + "\n\n" + json.dumps(DOC2) + "\n",
    ])
    @patch("fessctl.commands.documents.FessAPIClient")
    def test_accepts_array_wrapper_and_ndjson(self, mock_client_class, runner, tmp_path, text):
        mock_client = mock_client_class.return_value
        mock_client.bulk_index_documents.return_value = {"response": {"status": 0, "items": [{}, {}]}}
        path = tmp_path / "docs"
        path.write_text(text)

        result = runner.invoke(app, ["documents", "bulk", str(path)])

        assert result.exit_code == 0
        assert "2 document(s) indexed." in result.stdout
        mock_client.bulk_index_documents.assert_called_once_with([DOC1, DOC2])

    @patch("fessctl.commands.documents.FessAPIClient")
    def test_single_document_object(self, mock_client_class, runner, tmp_path):
        mock_client = mock_client_class.return_value
        mock_client.bulk_index_documents.return_value = {"response": {"status": 0, "items": [{}]}}
        path = tmp_path / "doc.json"
        path.write_text(json.dumps(DOC1))

        runner.invoke(app, ["documents", "bulk", str(path)])

        mock_client.bulk_index_documents.assert_called_once_with([DOC1])

    @patch("fessctl.commands.documents.FessAPIClient")
    def test_reads_stdin(self, mock_client_class, runner):
        mock_client = mock_client_class.return_value
        mock_client.bulk_index_documents.return_value = {"response": {"status": 0, "items": [{}]}}

        result = runner.invoke(app, ["documents", "bulk", "-"], input=json.dumps([DOC1]))

        assert result.exit_code == 0
        mock_client.bulk_index_documents.assert_called_once_with([DOC1])

    @pytest.mark.parametrize("text", ["not json", "[1, 2]", '{"documents": "x"}'])
    @patch("fessctl.commands.documents.FessAPIClient")
    def test_rejects_unparsable_input_without_calling_the_api(self, mock_client_class, runner, tmp_path, text):
        path = tmp_path / "bad"
        path.write_text(text)

        result = runner.invoke(app, ["documents", "bulk", str(path)])

        assert result.exit_code == 1
        assert "Cannot read documents" in result.stdout
        mock_client_class.return_value.bulk_index_documents.assert_not_called()

    @patch("fessctl.commands.documents.FessAPIClient")
    def test_missing_file(self, mock_client_class, runner, tmp_path):
        result = runner.invoke(app, ["documents", "bulk", str(tmp_path / "missing.json")])

        assert result.exit_code == 1
        assert "Cannot read documents" in result.stdout
        mock_client_class.return_value.bulk_index_documents.assert_not_called()

    @patch("fessctl.commands.documents.FessAPIClient")
    def test_partial_failure_lists_items_and_exits_with_status(self, mock_client_class, runner, tmp_path):
        mock_client_class.return_value.bulk_index_documents.return_value = {"response": {"status": 9, "items": [
            {"result": "CREATED", "id": "abc"},
            {"result": "BAD_REQUEST", "message": "mapper_parsing_exception"},
        ]}}
        path = tmp_path / "docs"
        path.write_text(json.dumps([DOC1, DOC2]))

        result = runner.invoke(app, ["documents", "bulk", str(path)])

        assert result.exit_code == 9
        assert "| 1 | CREATED | abc | - |" in result.stdout
        assert "| 2 | BAD_REQUEST | - | mapper_parsing_exception |" in result.stdout

    @pytest.mark.parametrize("output", ["json", "yaml"])
    @patch("fessctl.commands.documents.FessAPIClient")
    def test_api_failure_exits_with_status_in_every_format(self, mock_client_class, runner, tmp_path, output):
        mock_client_class.return_value.bulk_index_documents.return_value = {
            "response": {"status": 1, "message": "documents is empty."}}
        path = tmp_path / "docs"
        path.write_text("[]")

        result = runner.invoke(app, ["documents", "bulk", str(path), "--output", output])

        assert result.exit_code == 1
        assert "documents is empty." in result.stdout
