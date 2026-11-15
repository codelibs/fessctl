import json
import time
import uuid

import pytest
from typer.testing import CliRunner

from conftest import fess_version_at_least
from fessctl.commands.badword import badword_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_badword_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for BadWords.
    """
    # 1) Create a new badword
    suggest_word = f"badword-{uuid.uuid4().hex[:8]}"
    result = runner.invoke(
        badword_app,
        ["create", "--suggest-word", suggest_word, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    badword_id = create_resp["response"].get("id")
    assert badword_id, "No badword ID returned on create"

    # 2) Retrieve the created badword
    result = runner.invoke(
        badword_app,
        ["get", "--output", "json", "--", badword_id]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == badword_id
    assert setting.get("suggest_word") == suggest_word

    # 3) Update the badword's suggest_word
    new_suggest_word = f"updated-{suggest_word}"
    result = runner.invoke(
        badword_app,
        ["update", "--suggest-word", new_suggest_word, "--output", "json", "--", badword_id]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated suggest_word
    result = runner.invoke(
        badword_app,
        ["get", "--output", "json", "--", badword_id]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("suggest_word") == new_suggest_word

    # 5) List badwords and ensure the updated badword appears
    result = runner.invoke(
        badword_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert badword_id in ids

    # 6) Delete the badword
    result = runner.invoke(
        badword_app,
        ["delete", "--output", "json", "--", badword_id]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        badword_app,
        ["get", "--", badword_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve badword" in result.stdout.lower()


def wait_until(predicate, timeout=30):
    """Fess imports an uploaded CSV in the background; polls until predicate() holds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(1)
    return predicate()


def download_text(runner):
    result = runner.invoke(badword_app, ["download"])
    assert result.exit_code == 0, f"Download failed: {result.stdout}"
    return result.stdout_bytes.decode("utf-8")


def delete_badwords_containing(runner, marker):
    result = runner.invoke(badword_app, ["list", "--size", "1000", "--output", "json"])
    for item in json.loads(result.stdout)["response"].get("settings", []):
        if marker in item.get("suggest_word", ""):
            runner.invoke(badword_app, ["delete", "--output", "json", "--", item["id"]])


def test_badword_csv_download_and_upload(runner, fess_service, tmp_path):
    """
    Downloads the bad words as CSV, imports a CSV (the import runs in the background),
    and removes a word again with the "--" prefix.
    """
    marker = f"fctlcsv{uuid.uuid4().hex[:8]}"
    unicode_word = f"{marker}日本語"

    # download to a file: the CSV starts with its header, and an existing file needs --force
    target = tmp_path / "badword.csv"
    result = runner.invoke(badword_app, ["download", "--file", str(target)])
    assert result.exit_code == 0, f"Download failed: {result.stdout}"
    assert target.read_text(encoding="utf-8").startswith('"BadWord"')
    result = runner.invoke(badword_app, ["download", "--file", str(target)])
    assert result.exit_code != 0
    assert "already exists" in result.stdout
    result = runner.invoke(badword_app, ["download", "--file", str(target), "--force"])
    assert result.exit_code == 0

    source = tmp_path / "import.csv"
    source.write_text(f"BadWord\n{marker}\n{unicode_word}\n", encoding="utf-8")

    # declining the confirmation sends nothing
    result = runner.invoke(badword_app, ["upload", str(source)], input="n\n")
    assert result.exit_code != 0

    result = runner.invoke(badword_app, ["upload", str(tmp_path / "nope.csv"), "--yes"])
    assert result.exit_code != 0
    assert "not found" in result.stdout

    if fess_version_at_least(15, 6) and not fess_version_at_least(15, 9):
        # 15.6 to 15.8 cannot read a multipart PUT
        result = runner.invoke(badword_app, ["upload", str(source), "--yes"])
        assert result.exit_code != 0
        assert "not supported" in result.stdout
        return

    try:
        result = runner.invoke(badword_app, ["upload", str(source), "--yes", "--output", "json"])
        assert result.exit_code == 0, f"Upload failed: {result.stdout}"
        assert json.loads(result.stdout)["response"]["status"] == 0
        assert wait_until(lambda: unicode_word in download_text(runner)), "The import did not finish"
        assert f'"{marker}"' in download_text(runner)

        # a word with the "--" prefix is deleted, the other one is kept
        removal = tmp_path / "remove.csv"
        removal.write_text(f"BadWord\n--{marker}\n", encoding="utf-8")
        result = runner.invoke(badword_app, ["upload", str(removal), "--yes"])
        assert result.exit_code == 0, f"Upload failed: {result.stdout}"
        assert wait_until(lambda: f'"{marker}"' not in download_text(runner)), "The removal did not finish"
        assert f'"{unicode_word}"' in download_text(runner)
    finally:
        delete_badwords_containing(runner, marker)
    assert marker not in download_text(runner)
