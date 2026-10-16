"""
Unit tests for the theme command.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.theme import theme_app


@pytest.fixture
def runner():
    return CliRunner()


class TestThemeAvailable:
    @patch("fessctl.commands.theme.FessAPIClient")
    def test_available_text_output(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_available_themes.return_value = {"response": {"status": 0, "themes": [
            {"name": "filesearch", "version": "15.9.4"},
        ]}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(theme_app, ["available"])

        assert result.exit_code == 0
        assert "| filesearch | 15.9.4 |" in result.stdout

    @patch("fessctl.commands.theme.FessAPIClient")
    def test_available_empty(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.get_available_themes.return_value = {"response": {"status": 0, "themes": []}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(theme_app, ["available"])

        assert result.exit_code == 0
        assert "No Themes found." in result.stdout


class TestThemeInstall:
    @patch("fessctl.commands.theme.FessAPIClient")
    def test_install_success(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.install_theme.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(theme_app, ["install", "filesearch", "15.9.4"])

        assert result.exit_code == 0
        assert "installed successfully" in result.stdout
        mock_client.install_theme.assert_called_once_with("filesearch", "15.9.4")

    @patch("fessctl.commands.theme.FessAPIClient")
    def test_install_failure_exits_with_status(self, mock_client_class, runner):
        mock_client = Mock()
        mock_client.install_theme.return_value = {"response": {"status": 1, "message": "HTTP 404"}}
        mock_client_class.return_value = mock_client

        result = runner.invoke(theme_app, ["install", "nope", "0.0.1"])

        assert result.exit_code == 1
        assert "HTTP 404" in result.stdout


class TestThemeTimeout:
    @pytest.mark.parametrize("args", [["available"], ["install", "filesearch", "15.9.4"]])
    @patch("fessctl.commands.theme.FessAPIClient")
    def test_remote_calls_use_a_long_timeout(self, mock_client_class, runner, args):
        mock_client = Mock()
        mock_client.get_available_themes.return_value = {"response": {"status": 0, "themes": []}}
        mock_client.install_theme.return_value = {"response": {"status": 0}}
        mock_client_class.return_value = mock_client

        runner.invoke(theme_app, args)

        assert mock_client_class.call_args.kwargs["timeout"] >= 60
