"""
Unit tests for fessctl.cli module (ping command).
"""
import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.cli import app
from fessctl.api.client import FessAPIClientError


@pytest.fixture
def runner():
    """Provides a CliRunner instance for invoking commands."""
    return CliRunner()


class TestPingCommand:
    """Tests for the ping command."""

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_healthy_server_text_output(self, mock_client_class, runner):
        """Test ping with healthy server returns green status in text output."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "green", "timed_out": False}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping"])

        assert result.exit_code == 0
        assert "healthy" in result.stdout.lower()
        assert "green" in result.stdout.lower()

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_healthy_server_json_output(self, mock_client_class, runner):
        """Test ping with healthy server returns JSON output."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "green", "timed_out": False}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping", "--output", "json"])

        assert result.exit_code == 0
        response = json.loads(result.stdout)
        assert response["data"]["status"] == "green"

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_healthy_server_yaml_output(self, mock_client_class, runner):
        """Test ping with healthy server returns YAML output."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "green", "timed_out": False}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping", "--output", "yaml"])

        assert result.exit_code == 0
        assert "status: green" in result.stdout

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_yellow_status(self, mock_client_class, runner):
        """Test ping with yellow status shows warning."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "yellow", "timed_out": False}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping"])

        assert result.exit_code == 0
        assert "yellow" in result.stdout.lower()

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_red_status(self, mock_client_class, runner):
        """Test ping with red status returns error."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "red", "timed_out": False},
            "response": {"message": "Cluster is unhealthy"}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping"])

        assert result.exit_code == 1
        assert "red" in result.stdout.lower()

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_timed_out(self, mock_client_class, runner):
        """Test ping with timed_out=True returns error."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "green", "timed_out": True},
            "response": {"message": "Request timed out"}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping"])

        assert result.exit_code == 1
        assert "timed_out" in result.stdout.lower()

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_unknown_status(self, mock_client_class, runner):
        """Test ping with unknown status returns error."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "unknown", "timed_out": True},
            "response": {"message": ""}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping"])

        assert result.exit_code == 1

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_connection_error(self, mock_client_class, runner):
        """Test ping with connection error."""
        mock_client = Mock()
        mock_client.ping.side_effect = FessAPIClientError(
            status_code=-1, content="Connection refused"
        )
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping"])

        assert result.exit_code == 1
        assert "Connection refused" in result.stdout or "error" in result.stdout.lower()

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_generic_exception(self, mock_client_class, runner):
        """Test ping with generic exception."""
        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping"])

        assert result.exit_code == 1
        assert "Unexpected error" in result.stdout


class TestAppStructure:
    """Tests for the CLI app structure."""

    def test_app_has_ping_command(self, runner):
        """Test that the app has a ping command."""
        result = runner.invoke(app, ["--help"])

        assert "ping" in result.stdout

    def test_app_no_args_shows_help(self, runner):
        """Test that running app with no args shows help."""
        result = runner.invoke(app, [])

        # Should show help due to no_args_is_help=True
        assert "Usage:" in result.stdout or "Commands:" in result.stdout

    def test_app_has_subcommands(self, runner):
        """Test that the app has expected subcommands."""
        result = runner.invoke(app, ["--help"])

        # Check for some expected subcommands
        expected_commands = [
            "accesstoken", "badword", "group", "role", "user",
            "webconfig", "fileconfig", "scheduler"
        ]
        for cmd in expected_commands:
            assert cmd in result.stdout, f"Expected command '{cmd}' not found in help output"


class TestPingOutputFormats:
    """Additional tests for ping output formats."""

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_json_output_is_valid_json(self, mock_client_class, runner):
        """Test that JSON output is valid JSON."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "green", "timed_out": False, "number_of_nodes": 3}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping", "-o", "json"])

        # Should not raise
        data = json.loads(result.stdout)
        assert "data" in data

    @patch("fessctl.cli.FessAPIClient")
    def test_ping_short_output_flag(self, mock_client_class, runner):
        """Test that -o short flag works for output."""
        mock_client = Mock()
        mock_client.ping.return_value = {
            "data": {"status": "green", "timed_out": False}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["ping", "-o", "json"])

        assert result.exit_code == 0
        # Should be JSON
        json.loads(result.stdout)
