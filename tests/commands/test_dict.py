import json
import uuid

import pytest
from typer.testing import CliRunner

from conftest import fess_version_at_least
from fessctl.commands.dict import dict_app

# The dictionary file each type is exercised on (present in every supported Fess image).
DICT_PATHS = {
    "synonym": "synonym.txt",
    "mapping": "mapping.txt",
    "kuromoji": "ja/kuromoji.txt",
    "stopwords": "en/stopwords.txt",
    "protwords": "en/protwords.txt",
    "stemmeroverride": "en/stemmer_override.txt",
}

# Per type: arguments for create, arguments for update, and the fields (API names) each
# is expected to leave in the entry. "{u}" is replaced with a value unique to the test.
ENTRY_CASES = {
    "synonym": (
        ["--source", "{u}a", "--source", "{u}b", "--target", "{u}c"],
        ["--target", "{u}d", "--target", "{u}e"],
        {"inputs": "{u}a\n{u}b", "outputs": "{u}c"},
        {"inputs": "{u}a\n{u}b", "outputs": "{u}d\n{u}e"},
    ),
    "mapping": (
        ["--source", "{u}a", "--source", "{u}b", "--target", "{u}c"],
        ["--target", "{u}d"],
        {"inputs": "{u}a\n{u}b", "output": "{u}c"},
        {"inputs": "{u}a\n{u}b", "output": "{u}d"},
    ),
    "kuromoji": (
        ["--token", "{u}", "--segmentation", "{u}", "--reading", "エフ", "--pos", "カスタム名詞"],
        ["--reading", "エフシー"],
        {"token": "{u}", "segmentation": "{u}", "reading": "エフ", "pos": "カスタム名詞"},
        {"token": "{u}", "segmentation": "{u}", "reading": "エフシー", "pos": "カスタム名詞"},
    ),
    "stopwords": (
        ["--word", "{u}"], ["--word", "{u}x"], {"input": "{u}"}, {"input": "{u}x"},
    ),
    "protwords": (
        ["--word", "{u}"], ["--word", "{u}x"], {"input": "{u}"}, {"input": "{u}x"},
    ),
    "stemmeroverride": (
        ["--source", "{u}a", "--target", "{u}b"],
        ["--target", "{u}c"],
        {"input": "{u}a", "output": "{u}b"},
        {"input": "{u}a", "output": "{u}c"},
    ),
}


@pytest.fixture(scope="module")
def runner():
    """
    Provides a CliRunner instance for invoking commands.
    """
    return CliRunner()


def fill(value, u):
    """Replaces "{u}" in an argument list or an expected-fields dict."""
    if isinstance(value, dict):
        return {k: v.replace("{u}", u) for k, v in value.items()}
    return [v.replace("{u}", u) for v in value]


def invoke_json(runner, args):
    result = runner.invoke(dict_app, [*args, "--output", "json"])
    return result, json.loads(result.stdout)


@pytest.fixture(scope="module")
def dict_ids(runner, fess_service):
    """
    Maps each dictionary type to the ID of its test file, found with `dict list`.
    """
    result, resp = invoke_json(runner, ["list"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    paths = {(d["type"], d["path"]): d["id"] for d in resp["response"]["settings"]}
    missing = [t for t, p in DICT_PATHS.items() if (t, p) not in paths]
    assert not missing, f"The Fess under test has no dictionary file for {missing}"
    return {t: paths[(t, p)] for t, p in DICT_PATHS.items()}


def find_entries(runner, dict_type, dict_id, needle):
    """
    Returns the entries whose fields contain needle. Entry IDs are positions in the
    file and shift when an earlier entry is deleted, so entries are always looked
    up by their (unique) content.
    """
    result, resp = invoke_json(runner, [dict_type, "list", dict_id, "--size", "5000"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    return [e for e in resp["response"]["settings"] if needle in json.dumps(e, ensure_ascii=False)]


def test_dict_list(runner, dict_ids):
    result, resp = invoke_json(runner, ["list"])
    assert result.exit_code == 0, f"List failed: {result.stdout}"
    assert resp["response"]["status"] == 0
    assert all({"id", "type", "path"} <= d.keys() for d in resp["response"]["settings"])

    result, resp = invoke_json(runner, ["list", "--type", "kuromoji"])
    assert result.exit_code == 0
    assert [d["path"] for d in resp["response"]["settings"]] == ["ja/kuromoji.txt"]

    result = runner.invoke(dict_app, ["list", "--type", "synonym"])
    assert result.exit_code == 0
    assert "synonym.txt" in result.stdout


@pytest.mark.parametrize("dict_type", sorted(ENTRY_CASES))
def test_entry_crud_flow(runner, dict_ids, dict_type):
    """
    Tests the full Create, Read, Update, Delete flow of each dictionary type.
    """
    dict_id = dict_ids[dict_type]
    u = f"fctl{uuid.uuid4().hex[:8]}"
    create_args, update_args, after_create, after_update = (fill(x, u) for x in ENTRY_CASES[dict_type])
    try:
        # 1) Create. Fess before 15.9 answers with id "0", so find the entry by its content.
        result, resp = invoke_json(runner, [dict_type, "create", dict_id, *create_args])
        assert result.exit_code == 0, f"Create failed: {result.stdout}"
        assert resp["response"]["status"] == 0
        entries = find_entries(runner, dict_type, dict_id, u)
        assert len(entries) == 1, f"Created entry not found in the list: {entries}"
        item_id = entries[0]["id"]
        if resp["response"].get("id") not in (None, "", "0"):
            assert resp["response"]["id"] == str(item_id)

        # 2) Get
        result, resp = invoke_json(runner, [dict_type, "get", dict_id, str(item_id)])
        assert result.exit_code == 0, f"Get failed: {result.stdout}"
        setting = resp["response"]["setting"]
        assert setting["id"] == item_id
        assert {k: setting[k] for k in after_create} == after_create

        # 3) Update one field; the others must be kept
        result, resp = invoke_json(runner, [dict_type, "update", dict_id, str(item_id), *update_args])
        assert result.exit_code == 0, f"Update failed: {result.stdout}"
        assert resp["response"]["status"] == 0
        result, resp = invoke_json(runner, [dict_type, "get", dict_id, str(item_id)])
        setting = resp["response"]["setting"]
        assert {k: setting[k] for k in after_update} == after_update

        # 4) The text list shows it
        result = runner.invoke(dict_app, [dict_type, "list", dict_id, "--size", "5000"])
        assert result.exit_code == 0
        assert u in result.stdout

        # 5) Delete
        result, resp = invoke_json(runner, [dict_type, "delete", dict_id, str(item_id)])
        assert result.exit_code == 0, f"Delete failed: {result.stdout}"
        assert find_entries(runner, dict_type, dict_id, u) == []
    finally:
        # Entry IDs shift on delete, so a leftover is looked up again by its content.
        for entry in find_entries(runner, dict_type, dict_id, u):
            runner.invoke(dict_app, [dict_type, "delete", dict_id, str(entry["id"])])


def test_entry_errors(runner, dict_ids):
    dict_id = dict_ids["synonym"]

    result = runner.invoke(dict_app, ["synonym", "get", dict_id, "99999999"])
    assert result.exit_code != 0
    assert "failed to retrieve synonym entry" in result.stdout.lower()

    result = runner.invoke(dict_app, ["synonym", "update", dict_id, "99999999", "--source", "fctl"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()

    result = runner.invoke(dict_app, ["synonym", "delete", dict_id, "99999999"])
    assert result.exit_code != 0
    assert "failed to delete synonym entry" in result.stdout.lower()

    # An unknown dictionary ID lists nothing in every version
    result = runner.invoke(dict_app, ["synonym", "list", "nosuchdict"])
    assert result.exit_code == 0
    assert "No synonym entries found." in result.stdout

    # A source word may not contain a comma. The check exists since Fess 15.9; older
    # versions fail on it with a server error, so only the failure is common.
    u = f"fctl{uuid.uuid4().hex[:8]}"
    try:
        result = runner.invoke(dict_app, ["synonym", "create", dict_id, "--source", f"{u},x", "--target", "y"])
        assert result.exit_code != 0
    finally:
        for entry in find_entries(runner, "synonym", dict_id, u):
            runner.invoke(dict_app, ["synonym", "delete", dict_id, str(entry["id"])])

    # Fess before 15.9 reports success when creating in an unknown dictionary
    if fess_version_at_least(15, 9):
        result = runner.invoke(dict_app, ["synonym", "create", "nosuchdict", "--source", "fctl", "--target", "y"])
        assert result.exit_code != 0


def test_download_error(runner, dict_ids):
    result = runner.invoke(dict_app, ["synonym", "download", "nosuchdict"])
    assert result.exit_code != 0
    assert "failed to download synonym dictionary" in result.stdout.lower()


def test_download_and_upload_flow(runner, dict_ids, tmp_path):
    """
    Downloads a dictionary file, replaces it with a modified copy, and restores it.
    Fess 15.6 to 15.8 cannot receive uploads at all (the server cannot read a multipart PUT).
    """
    dict_id = dict_ids["protwords"]
    original = tmp_path / "original.txt"
    result = runner.invoke(dict_app, ["protwords", "download", dict_id, "--file", str(original)])
    assert result.exit_code == 0, f"Download failed: {result.stdout}"

    # An existing file is not overwritten without --force
    result = runner.invoke(dict_app, ["protwords", "download", dict_id, "--file", str(original)])
    assert result.exit_code != 0
    assert "already exists" in result.stdout

    result = runner.invoke(dict_app, ["protwords", "download", dict_id])
    assert result.exit_code == 0
    assert result.stdout_bytes == original.read_bytes()

    u = f"fctl{uuid.uuid4().hex[:8]}"
    modified = tmp_path / "modified.txt"
    modified.write_bytes(original.read_bytes() + f"{u}\n".encode())

    if fess_version_at_least(15, 6) and not fess_version_at_least(15, 9):
        result = runner.invoke(dict_app, ["protwords", "upload", dict_id, str(modified), "--yes"])
        assert result.exit_code != 0
        assert "not supported" in result.stdout
        assert runner.invoke(dict_app, ["protwords", "download", dict_id]).stdout_bytes == original.read_bytes()
        return

    try:
        result, resp = invoke_json(runner, ["protwords", "upload", dict_id, str(modified), "--yes"])
        assert result.exit_code == 0, f"Upload failed: {result.stdout}"
        assert resp["response"]["status"] == 0
        downloaded = runner.invoke(dict_app, ["protwords", "download", dict_id])
        assert downloaded.stdout_bytes == modified.read_bytes()
        assert len(find_entries(runner, "protwords", dict_id, u)) == 1
    finally:
        result = runner.invoke(dict_app, ["protwords", "upload", dict_id, str(original), "--yes"])
        assert result.exit_code == 0, f"Restoring the dictionary failed: {result.stdout}"
    assert runner.invoke(dict_app, ["protwords", "download", dict_id]).stdout_bytes == original.read_bytes()
    assert find_entries(runner, "protwords", dict_id, u) == []

    # Fess rejects an upload to an unknown dictionary
    result = runner.invoke(dict_app, ["protwords", "upload", "nosuchdict", str(original), "--yes"])
    assert result.exit_code != 0
