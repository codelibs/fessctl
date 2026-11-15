import json
import time
import uuid

import pytest
from typer.testing import CliRunner

from conftest import fess_version_at_least
from fessctl.commands.elevateword import elevateword_app


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def test_elevateword_crud_flow(runner, fess_service):
    """
    Tests the full Create, Read, Update, Delete (CRUD) flow for ElevateWords.
    """
    # 1) Create a new elevateword
    suggest_word = f"elevate-{uuid.uuid4().hex[:8]}"
    boost = "10.0"
    version_no = "1"
    result = runner.invoke(
        elevateword_app,
        ["create", "--suggest-word", suggest_word, "--boost", boost, "--version-no", version_no, "--output", "json"]
    )
    assert result.exit_code == 0, f"Create failed: {result.stdout}"
    create_resp = json.loads(result.stdout)
    assert create_resp.get("response", {}).get("status") == 0
    elevateword_id = create_resp["response"].get("id")
    assert elevateword_id, "No elevateword ID returned on create"

    # 2) Retrieve the created elevateword
    result = runner.invoke(
        elevateword_app,
        ["get", "--output", "json", "--", elevateword_id]
    )
    assert result.exit_code == 0, f"Get failed: {result.stdout}"
    get_resp = json.loads(result.stdout)
    assert get_resp.get("response", {}).get("status") == 0
    setting = get_resp["response"].get("setting", {})
    assert setting.get("id") == elevateword_id
    assert setting.get("suggest_word") == suggest_word

    # 3) Update the elevateword's boost
    new_boost = "20.0"
    result = runner.invoke(
        elevateword_app,
        ["update", "--boost", new_boost, "--output", "json", "--", elevateword_id]
    )
    assert result.exit_code == 0, f"Update failed: {result.stdout}"
    update_resp = json.loads(result.stdout)
    assert update_resp.get("response", {}).get("status") == 0

    # 4) Retrieve again and verify updated boost
    result = runner.invoke(
        elevateword_app,
        ["get", "--output", "json", "--", elevateword_id]
    )
    assert result.exit_code == 0, f"Get after update failed: {result.stdout}"
    get_after = json.loads(result.stdout)
    setting_after = get_after["response"].get("setting", {})
    assert setting_after.get("boost") == float(new_boost)

    # 5) List elevatewords and ensure the updated elevateword appears
    result = runner.invoke(
        elevateword_app,
        ["list", "--output", "json"]
    )
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    list_resp = json.loads(result.stdout)
    assert list_resp.get("response", {}).get("status") == 0
    settings = list_resp["response"].get("settings", [])
    ids = [g.get("id") for g in settings]
    assert elevateword_id in ids

    # 6) Delete the elevateword
    result = runner.invoke(
        elevateword_app,
        ["delete", "--output", "json", "--", elevateword_id]
    )
    assert result.exit_code == 0, f"Delete failed: {result.stdout}"
    del_resp = json.loads(result.stdout)
    assert del_resp.get("response", {}).get("status") == 0

    # 7) Verify that get now fails
    result = runner.invoke(
        elevateword_app,
        ["get", "--", elevateword_id]
    )
    assert result.exit_code != 0
    assert "failed to retrieve elevateword" in result.stdout.lower()


def wait_until(predicate, timeout=30):
    """Fess imports an uploaded CSV in the background; polls until predicate() holds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(1)
    return predicate()


def download_text(runner):
    result = runner.invoke(elevateword_app, ["download"])
    assert result.exit_code == 0, f"Download failed: {result.stdout}"
    return result.stdout_bytes.decode("utf-8")


def delete_elevatewords_containing(runner, marker):
    result = runner.invoke(elevateword_app, ["list", "--size", "1000", "--output", "json"])
    for item in json.loads(result.stdout)["response"].get("settings", []):
        if marker in item.get("suggest_word", ""):
            runner.invoke(elevateword_app, ["delete", "--output", "json", "--", item["id"]])


def test_elevateword_csv_download_and_upload(runner, fess_service, tmp_path):
    """
    Downloads the elevate words as CSV and imports a CSV (the import runs in the background).
    """
    marker = f"fctlcsv{uuid.uuid4().hex[:8]}"
    unicode_word = f"{marker}日本語"

    # download to a file: the CSV starts with its header, and an existing file needs --force
    target = tmp_path / "elevate.csv"
    result = runner.invoke(elevateword_app, ["download", "--file", str(target)])
    assert result.exit_code == 0, f"Download failed: {result.stdout}"
    assert target.read_text(encoding="utf-8").startswith('"SuggestWord","Reading","Permissions","Labels","Boost"')
    result = runner.invoke(elevateword_app, ["download", "--file", str(target)])
    assert result.exit_code != 0
    assert "already exists" in result.stdout
    result = runner.invoke(elevateword_app, ["download", "--file", str(target), "--force"])
    assert result.exit_code == 0

    source = tmp_path / "import.csv"
    source.write_text(
        "SuggestWord,Reading,Permissions,Labels,Boost\n"
        f"{marker},yomi,,,5.5\n"
        f"{unicode_word},にほんご,,,2\n",
        encoding="utf-8")

    # declining the confirmation sends nothing
    result = runner.invoke(elevateword_app, ["upload", str(source)], input="n\n")
    assert result.exit_code != 0

    result = runner.invoke(elevateword_app, ["upload", str(tmp_path / "nope.csv"), "--yes"])
    assert result.exit_code != 0
    assert "not found" in result.stdout

    if fess_version_at_least(15, 6) and not fess_version_at_least(15, 9):
        # 15.6 to 15.8 cannot read a multipart PUT
        result = runner.invoke(elevateword_app, ["upload", str(source), "--yes"])
        assert result.exit_code != 0
        assert "not supported" in result.stdout
        return

    try:
        result = runner.invoke(elevateword_app, ["upload", str(source), "--yes", "--output", "json"])
        assert result.exit_code == 0, f"Upload failed: {result.stdout}"
        assert json.loads(result.stdout)["response"]["status"] == 0
        assert wait_until(lambda: unicode_word in download_text(runner)), "The import did not finish"
        assert f'"{marker}","yomi","","","5.5"' in download_text(runner)
        assert f'"{unicode_word}","にほんご","","","2.0"' in download_text(runner)

        # (Rows for existing words overwrite them and a row with neither reading nor boost deletes the
        # word, but on some releases Fess then leaves such a word in the suggest index, which would break
        # test_suggest, so only the plain import is exercised here.)
    finally:
        delete_elevatewords_containing(runner, marker)
    assert marker not in download_text(runner)
