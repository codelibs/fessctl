"""
Unit tests for the file downloads (log and backup) of fessctl.api.client, run against a local HTTP server.
"""
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import Mock

import pytest

from fessctl.api.client import FessAPIClient, FessAPIClientError
from fessctl.config.settings import Settings

# path -> (status, content type, body) of what the fake Fess answers
ROUTES = {
    "/api/admin/log/file/ZmVzcy5sb2c=": (200, "application/octet-stream", b"log line\n"),
    "/api/admin/log/file/YmFk": (400, "application/json;charset=UTF-8", b'{"response":{"message":"Could not find bad.","status":1}}'),
    # an id with an extension is only served with the trailing slash
    "/api/admin/backup/file/fess_config.bulk/": (200, "application/octet-stream", b'{"index":{}}\n{"a":1}\n'),
    "/api/admin/backup/file/search_log.ndjson/": (200, "application/x-ndjson", b'{"search-word":"x"}\n'),
    "/api/admin/backup/file/nope/": (400, "application/json;charset=UTF-8", b'{"response":{"message":"Could not find any backup index.","status":1}}'),
}


class Handler(BaseHTTPRequestHandler):
    requests = []

    def do_GET(self):
        Handler.requests.append((self.path, self.headers.get("Authorization")))
        status, content_type, body = ROUTES.get(self.path, (404, "text/plain;charset=UTF-8", b"Not Found."))
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def endpoint():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def client(endpoint):
    settings = Mock(spec=Settings)
    settings.fess_endpoint = endpoint
    settings.access_token = "test-token"
    settings.fess_version = "15.9.0"
    Handler.requests.clear()
    return FessAPIClient(settings)


def test_download_log_file_writes_the_body(client, tmp_path):
    dest = tmp_path / "fess.log"

    result = client.download_log_file("ZmVzcy5sb2c=", dest)

    assert result == {"response": {"status": 0, "path": str(dest), "size": 9}}
    assert dest.read_bytes() == b"log line\n"
    assert list(tmp_path.iterdir()) == [dest]
    assert Handler.requests == [("/api/admin/log/file/ZmVzcy5sb2c=", "Bearer test-token")]


def test_download_backup_file_requests_the_id_with_a_trailing_slash(client, tmp_path):
    dest = tmp_path / "fess_config.bulk"

    result = client.download_backup_file("fess_config.bulk", dest)

    assert result["response"]["status"] == 0
    assert dest.read_bytes() == b'{"index":{}}\n{"a":1}\n'
    assert Handler.requests == [("/api/admin/backup/file/fess_config.bulk/", "Bearer test-token")]


def test_download_backup_ndjson_is_not_mistaken_for_a_json_error(client, tmp_path):
    dest = tmp_path / "search_log.ndjson"

    result = client.download_backup_file("search_log.ndjson", dest)

    assert result["response"]["status"] == 0
    assert dest.read_bytes() == b'{"search-word":"x"}\n'


def test_download_json_error_is_returned_and_writes_no_file(client, tmp_path):
    dest = tmp_path / "nope"

    result = client.download_backup_file("nope", dest)

    assert result == {"response": {"message": "Could not find any backup index.", "status": 1}}
    assert list(tmp_path.iterdir()) == []


def test_download_non_json_error_raises(client, tmp_path):
    dest = tmp_path / "x.log"

    with pytest.raises(FessAPIClientError) as e:
        client.download_log_file("eA==", dest)

    assert e.value.status_code == 404
    assert "Not Found." in str(e.value)
    assert list(tmp_path.iterdir()) == []


def test_download_unreachable_server_raises_and_writes_no_file(tmp_path):
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://127.0.0.1:1"
    settings.access_token = "test-token"
    settings.fess_version = "15.9.0"

    with pytest.raises(FessAPIClientError) as e:
        FessAPIClient(settings).download_log_file("ZmVzcy5sb2c=", tmp_path / "x.log")

    assert e.value.status_code == -1
    assert list(tmp_path.iterdir()) == []
