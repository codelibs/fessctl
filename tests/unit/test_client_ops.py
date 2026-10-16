"""
Unit tests for the systeminfo, stats, log, backup and suggest listing/deleting methods of fessctl.api.client.
"""
from unittest.mock import Mock, patch

import pytest

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings


@pytest.fixture
def client():
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://localhost:8080"
    settings.access_token = "test-token"
    settings.fess_version = "15.9.0"
    return FessAPIClient(settings)


@pytest.mark.parametrize("method,path", [
    ("get_systeminfo", "/api/admin/systeminfo"),
    ("get_stats", "/api/admin/stats"),
    ("get_log_files", "/api/admin/log/files"),
    ("get_backup_files", "/api/admin/backup/files"),
    ("get_suggest_info", "/api/admin/suggest"),
])
@patch("httpx.get")
def test_get_methods_request_the_path(mock_get, client, method, path):
    mock_get.return_value.json.return_value = {"response": {"status": 0}}

    assert getattr(client, method)() == {"response": {"status": 0}}

    assert mock_get.call_args[0][0] == f"http://localhost:8080{path}"
    assert mock_get.call_args[1]["headers"]["Authorization"] == "Bearer test-token"


@pytest.mark.parametrize("method,path", [
    ("delete_all_suggest_words", "/api/admin/suggest/all"),
    ("delete_document_suggest_words", "/api/admin/suggest/document"),
    ("delete_query_suggest_words", "/api/admin/suggest/query"),
])
@patch("httpx.delete")
def test_suggest_delete_methods_request_the_path(mock_delete, client, method, path):
    mock_delete.return_value.json.return_value = {"response": {"status": 0}}

    assert getattr(client, method)() == {"response": {"status": 0}}

    assert mock_delete.call_args[0][0] == f"http://localhost:8080{path}"
