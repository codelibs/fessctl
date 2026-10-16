import json

import pytest
from typer.testing import CliRunner

from conftest import fess_version_at_least
from fessctl.commands.storage import storage_app

# The Fess under test has no object storage configured, so these tests cover how the
# commands behave without a backend. Reading and writing objects is covered by the unit tests
# and was verified by hand against an S3-compatible server.


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_storage_list_without_backend(runner, fess_service):
    result = runner.invoke(storage_app, ["list"])
    if fess_version_at_least(15, 9):
        # 15.9 reports a storage it cannot reach; the message names the plugin to install
        assert result.exit_code != 0
        assert "storage access error" in result.stdout.lower()
    else:
        # earlier versions answer an unreachable storage with an empty list
        assert result.exit_code == 0
        assert "No Storage items found." in result.stdout


def test_storage_list_json_without_backend(runner, fess_service):
    result = runner.invoke(storage_app, ["list", "docs/sub", "--output", "json"])
    resp = json.loads(result.stdout)
    if fess_version_at_least(15, 9):
        assert result.exit_code != 0
        assert resp["response"]["status"] != 0
    else:
        assert result.exit_code == 0
        assert resp["response"]["items"] == []


def test_storage_delete_aborts_without_confirmation(runner, fess_service):
    result = runner.invoke(storage_app, ["delete", "no/such/object.txt"], input="n\n")
    assert result.exit_code != 0


def test_storage_download_refuses_to_overwrite(runner, fess_service, tmp_path):
    target = tmp_path / "existing.txt"
    target.write_text("keep")
    result = runner.invoke(storage_app, ["download", "no/such/object.txt", "--file", str(target)])
    assert result.exit_code != 0
    assert target.read_text() == "keep"


def test_storage_download_missing_object_fails(runner, fess_service, tmp_path):
    target = tmp_path / "out.txt"
    result = runner.invoke(storage_app, ["download", "no/such/object.txt", "--file", str(target)])
    assert result.exit_code != 0
    assert "failed to download storage object" in result.stdout.lower()
    assert not target.exists()


def test_storage_upload_without_backend_fails(runner, fess_service, tmp_path):
    source = tmp_path / "fessctl-upload-test.txt"
    source.write_text("fessctl")
    result = runner.invoke(storage_app, ["upload", str(source), "--dir", "fessctl-test"])
    # 15.6 to 15.8 cannot receive uploads at all; the others fail on the missing backend
    assert result.exit_code != 0
    assert "failed to upload storage object" in result.stdout.lower()
