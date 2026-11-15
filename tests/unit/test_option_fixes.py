"""
Small CLI behaviours: reqheader get shows the header itself; create commands no longer demand a --version-no
that Fess ignores on create.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.elevateword import elevateword_app
from fessctl.commands.keymatch import keymatch_app
from fessctl.commands.labeltype import labeltype_app
from fessctl.commands.relatedquery import relatedquery_app
from fessctl.commands.reqheader import reqheader_app

runner = CliRunner()


@patch("fessctl.commands.reqheader.FessAPIClient")
def test_reqheader_get_shows_name_and_value(mock_client_class):
    client = Mock()
    client.get_reqheader.return_value = {"response": {"status": 0, "setting": {
        "id": "rh1", "name": "X-Trace", "value": "abc", "web_config_id": "w1", "version_no": 1}}}
    mock_client_class.return_value = client

    result = runner.invoke(reqheader_app, ["get", "rh1"])

    assert result.exit_code == 0
    assert "X-Trace" in result.stdout
    assert "abc" in result.stdout
    assert "hostname" not in result.stdout
    assert "auth_realm" not in result.stdout


CREATE_WITHOUT_VERSION_NO = [
    ("keymatch", keymatch_app, ["--term", "t", "--query", "q", "--max-size", "1", "--boost", "1"], "create_keymatch"),
    ("elevateword", elevateword_app, ["--suggest-word", "w", "--boost", "1"], "create_elevateword"),
    ("labeltype", labeltype_app, ["--name", "n", "--value", "v"], "create_labeltype"),
    ("relatedquery", relatedquery_app, ["--term", "t", "--queries", "q"], "create_relatedquery"),
]


@pytest.mark.parametrize("module,app,args,method", CREATE_WITHOUT_VERSION_NO, ids=[c[0] for c in CREATE_WITHOUT_VERSION_NO])
def test_create_without_version_no(module, app, args, method):
    with patch(f"fessctl.commands.{module}.FessAPIClient") as client_class:
        client = Mock()
        getattr(client, method).return_value = {"response": {"status": 0, "id": "x"}}
        client_class.return_value = client

        result = runner.invoke(app, ["create", *args])

        assert result.exit_code == 0, result.stdout
        assert getattr(client, method).call_args[0][0]["version_no"] == 0


def test_user_list_messages_talk_about_users():
    from fessctl.commands.user import user_app

    with patch("fessctl.commands.user.FessAPIClient") as client_class:
        client = Mock()
        client_class.return_value = client

        client.list_users.return_value = {"response": {"status": 0, "settings": []}}
        empty = runner.invoke(user_app, ["list"])
        assert "No users found." in empty.stdout

        client.list_users.return_value = {"response": {"status": 1, "message": "boom"}}
        failed = runner.invoke(user_app, ["list"])
        assert "Failed to list users." in failed.stdout
