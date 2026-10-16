"""
Unit tests for the plugin command.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.plugin import plugin_app

PLUGINS = {"response": {"status": 0, "plugins": [
    {"name": "fess-ds-csv", "id": "fess-ds-csv:15.9.0", "type": "fess-ds", "version": "15.9.0"},
]}}


@pytest.fixture
def runner():
    return CliRunner()


class TestPluginList:
    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_installed_text_output(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_installed_plugins.return_value = PLUGINS
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["installed"])

        assert result.exit_code == 0
        assert "| fess-ds-csv | 15.9.0 | fess-ds |" in result.stdout

    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_available_empty(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_available_plugins.return_value = {"response": {"status": 0, "plugins": []}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["available"])

        assert result.exit_code == 0
        assert "No Available Plugins found." in result.stdout

    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_available_json_output(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_available_plugins.return_value = PLUGINS
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["available", "--output", "json"])

        assert '"fess-ds-csv"' in result.stdout

    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_installed_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_installed_plugins.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["installed"])

        assert result.exit_code == 3
        assert "Unauthorized request." in result.stdout


class TestPluginInstall:
    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_install(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.install_plugin.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["install", "fess-ds-csv", "15.9.0"])

        assert result.exit_code == 0
        assert "requested" in result.stdout
        mock_client.install_plugin.assert_called_once_with("fess-ds-csv", "15.9.0")

    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_install_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.install_plugin.return_value = {"response": {"status": 1, "message": "invalid name or version"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["install", "nope", "0.0.1"])

        assert result.exit_code == 1
        assert "invalid name or version" in result.stdout


class TestPluginUninstall:
    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_uninstall_aborts_without_confirmation(self, mock_client_class, runner):
        result = runner.invoke(plugin_app, ["uninstall", "fess-ds-csv", "15.9.0"], input="n\n")

        assert result.exit_code != 0
        mock_client_class.return_value.uninstall_plugin.assert_not_called()

    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_uninstall_confirmed(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.uninstall_plugin.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["uninstall", "fess-ds-csv", "15.9.0"], input="y\n")

        assert result.exit_code == 0
        mock_client.uninstall_plugin.assert_called_once_with("fess-ds-csv", "15.9.0")

    @patch("fessctl.commands.plugin.FessAPIClient")
    def test_uninstall_with_yes_skips_prompt(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.uninstall_plugin.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(plugin_app, ["uninstall", "fess-ds-csv", "15.9.0", "--yes"])

        assert result.exit_code == 0
        assert "requested" in result.stdout


@pytest.mark.parametrize("output", ["json", "yaml"])
@patch("fessctl.commands.plugin.FessAPIClient")
def test_failure_exits_with_status_in_every_format(mock_client_class, output):
    mock_client = Mock()
    failure = {"response": {"status": 1, "message": "invalid name or version"}}
    mock_client.install_plugin.return_value = failure
    mock_client.get_available_plugins.return_value = failure
    mock_client_class.return_value = mock_client
    runner = CliRunner()

    assert runner.invoke(plugin_app, ["install", "x", "1", "--output", output]).exit_code == 1
    assert runner.invoke(plugin_app, ["available", "--output", output]).exit_code == 1


def test_available_uses_a_long_timeout():
    """`available` makes Fess query the remote plugin repositories."""
    from unittest.mock import Mock, patch

    from typer.testing import CliRunner

    from fessctl.commands.plugin import plugin_app

    with patch("fessctl.commands.plugin.FessAPIClient") as mock_client_class:
        mock_client = Mock()
        mock_client.get_available_plugins.return_value = {"response": {"status": 0, "plugins": []}}
        mock_client_class.return_value = mock_client

        CliRunner().invoke(plugin_app, ["available"])

        assert mock_client_class.call_args.kwargs["timeout"] >= 60
