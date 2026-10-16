import json

import pytest
from typer.testing import CliRunner

from fessctl.commands.log import log_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def _fess_log(runner):
    """
    The `fess.log` entry of the log list. Fess logs to it from startup, so it always exists.
    """
    result = runner.invoke(log_app, ["list", "--output", "json"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    resp = json.loads(result.stdout).get("response", {})
    assert resp.get("status") == 0
    files = resp.get("files", [])
    assert all({"name", "id", "lastModified"} <= f.keys() for f in files)
    matches = [f for f in files if f["name"] == "fess.log"]
    assert matches, f"fess.log is not listed: {[f['name'] for f in files]}"
    return matches[0]


def test_log_list_text(runner, fess_service):
    result = runner.invoke(log_app, ["list"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    assert "| fess.log |" in result.stdout


def test_log_download(runner, fess_service, tmp_path):
    entry = _fess_log(runner)
    dest = tmp_path / "fess.log"

    result = runner.invoke(log_app, ["download", entry["id"], "--dest", str(dest), "--output", "json"])
    assert result.exit_code == 0, f"Download failed: {result.stdout}"
    resp = json.loads(result.stdout).get("response", {})
    assert resp.get("status") == 0
    assert dest.is_file()
    assert resp["size"] == dest.stat().st_size

    # An existing destination is not overwritten unless --force is given.
    dest.write_text("keep")
    result = runner.invoke(log_app, ["download", entry["id"], "--dest", str(dest)])
    assert result.exit_code != 0
    assert "--force" in result.stdout
    assert dest.read_text() == "keep"

    result = runner.invoke(log_app, ["download", entry["id"], "--dest", str(dest), "--force"])
    assert result.exit_code == 0, f"Forced download failed: {result.stdout}"
    assert dest.read_text() != "keep"


def test_log_download_unknown_id(runner, fess_service, tmp_path):
    dest = tmp_path / "no-such.log"
    # base64 of "no-such.log"
    result = runner.invoke(log_app, ["download", "bm8tc3VjaC5sb2c=", "--dest", str(dest)])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()
    assert not dest.exists()
