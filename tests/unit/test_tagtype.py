"""
Unit tests for the tagtype command.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.tagtype import tagtype_app


@pytest.fixture
def runner():
    return CliRunner()


def _stored_tag():
    return {
        "response": {
            "status": 0,
            "setting": {
                "id": "tag-001",
                "name": "work",
                "owner": "taro",
                "paths": "https://a.example.com/\nhttps://b.example.com/",
                "permissions": "{user}taro",
                "virtual_host": "",
                "sort_order": 0,
                "seq_no": 7,
                "primary_term": 1,
                "crud_mode": None,
            },
        }
    }


class TestTagTypeUpdate:

    @patch("fessctl.commands.tagtype.FessAPIClient")
    def test_update_keeps_unchanged_fields(self, mock_client_class, runner):
        """The PUT replaces the whole tag, so the paths and seq_no read by GET are sent back."""
        mock_client = Mock()
        mock_client.get_tagtype.return_value = _stored_tag()
        mock_client.update_tagtype.return_value = {"response": {"status": 0, "id": "tag-001"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(tagtype_app, ["update", "--sort-order", "3", "tag-001"])
        assert result.exit_code == 0, result.stdout
        sent = mock_client.update_tagtype.call_args.args[0]
        assert sent["crud_mode"] == 2
        assert sent["sort_order"] == 3
        assert sent["paths"] == "https://a.example.com/\nhttps://b.example.com/"
        assert sent["permissions"] == "{user}taro"
        assert sent["seq_no"] == 7
        assert sent["primary_term"] == 1

    @patch("fessctl.commands.tagtype.FessAPIClient")
    def test_update_replaces_paths_and_reports_new_id(self, mock_client_class, runner):
        """A rename gives the tag a new id, which is the one reported."""
        mock_client = Mock()
        mock_client.get_tagtype.return_value = _stored_tag()
        mock_client.update_tagtype.return_value = {"response": {"status": 0, "id": "tag-002"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            tagtype_app,
            ["update", "--name", "home", "--path", "https://c.example.com/", "tag-001"],
        )
        assert result.exit_code == 0, result.stdout
        sent = mock_client.update_tagtype.call_args.args[0]
        assert sent["name"] == "home"
        assert sent["paths"] == "https://c.example.com/"
        assert "tag-002" in result.stdout

    @patch("fessctl.commands.tagtype.FessAPIClient")
    def test_update_reports_conflict(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_tagtype.return_value = _stored_tag()
        mock_client.update_tagtype.return_value = {
            "response": {"status": 1, "message": "The tag was changed concurrently."}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(tagtype_app, ["update", "--sort-order", "1", "tag-001"])
        assert result.exit_code == 1
        assert "changed concurrently" in result.stdout

    @patch("fessctl.commands.tagtype.FessAPIClient")
    def test_update_missing_tag(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_tagtype.return_value = {"response": {"status": 1, "message": "not found"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(tagtype_app, ["update", "--sort-order", "1", "missing"])
        assert result.exit_code == 1
        mock_client.update_tagtype.assert_not_called()


class TestTagTypeCreate:

    @patch("fessctl.commands.tagtype.FessAPIClient")
    def test_create_joins_paths_and_permissions(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.create_tagtype.return_value = {"response": {"status": 0, "id": "tag-001"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(tagtype_app, [
            "create", "--name", "work", "--owner", "taro",
            "--path", "https://a.example.com/", "--path", "https://b.example.com/",
            "--permission", "{user}taro",
        ])
        assert result.exit_code == 0, result.stdout
        sent = mock_client.create_tagtype.call_args.args[0]
        assert sent == {
            "crud_mode": 1,
            "name": "work",
            "owner": "taro",
            "sort_order": 0,
            "paths": "https://a.example.com/\nhttps://b.example.com/",
            "permissions": "{user}taro",
        }
        assert "tag-001" in result.stdout


class TestTagTypeList:

    @patch("fessctl.commands.tagtype.FessAPIClient")
    def test_list_text_output(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.list_tagtypes.return_value = {
            "response": {"status": 0, "settings": [{"id": "tag-001", "name": "work", "owner": "taro"}]}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(tagtype_app, ["list"])
        assert result.exit_code == 0, result.stdout
        assert "tag-001" in result.stdout
        assert "taro" in result.stdout
