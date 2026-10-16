import json

import pytest
from typer.testing import CliRunner

from fessctl.commands.backup import backup_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_backup_list(runner, fess_service):
    result = runner.invoke(backup_app, ["list", "--output", "json"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    resp = json.loads(result.stdout).get("response", {})
    assert resp.get("status") == 0
    ids = [f["id"] for f in resp.get("files", [])]
    for expected in ("fess_config.bulk", "system.properties", "search_log.ndjson"):
        assert expected in ids

    result = runner.invoke(backup_app, ["list"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    assert "| fess_config.bulk | fess_config.bulk |" in result.stdout


@pytest.mark.parametrize("backup_id", ["fess_config.bulk", "system.properties", "search_log.ndjson"])
def test_backup_download(runner, fess_service, tmp_path, backup_id):
    """
    An index dump, the system properties and a search log, all ids with an extension.
    The search log may be empty, so only the transfer is checked.
    """
    dest = tmp_path / backup_id

    result = runner.invoke(backup_app, ["download", backup_id, "--dest", str(dest), "--output", "json"])
    assert result.exit_code == 0, f"Download failed: {result.stdout}"
    resp = json.loads(result.stdout).get("response", {})
    assert resp.get("status") == 0
    assert dest.is_file()
    assert resp["size"] == dest.stat().st_size
    if backup_id == "fess_config.bulk":
        assert '"_index":"fess_config' in dest.read_text()

    # An existing destination is not overwritten unless --force is given.
    result = runner.invoke(backup_app, ["download", backup_id, "--dest", str(dest)])
    assert result.exit_code != 0
    assert "--force" in result.stdout
    result = runner.invoke(backup_app, ["download", backup_id, "--dest", str(dest), "--force"])
    assert result.exit_code == 0, f"Forced download failed: {result.stdout}"


def test_backup_download_unknown_id(runner, fess_service, tmp_path):
    dest = tmp_path / "no-such-backup"
    result = runner.invoke(backup_app, ["download", "no-such-backup", "--dest", str(dest)])
    assert result.exit_code != 0
    assert "failed to download backup file" in result.stdout.lower()
    assert not dest.exists()
