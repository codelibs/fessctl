"""
Unit tests for scheduler start command jobLogId support.
"""
import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.scheduler import scheduler_app


@pytest.fixture
def runner():
    return CliRunner()


class TestSchedulerStartJobLogId:
    """Tests for jobLogId in scheduler start response."""

    @patch("fessctl.commands.scheduler.FessAPIClient")
    def test_start_with_job_log_id_text_output(self, mock_client_class, runner):
        """Test that jobLogId is displayed in text output when present."""
        mock_client = Mock()
        mock_client.start_scheduler.return_value = {
            "response": {"status": 0, "jobLogId": "abc123def456"}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(scheduler_app, ["start", "sched-001"])
        assert result.exit_code == 0
        assert "started successfully" in result.stdout
        assert "Job Log ID: abc123def456" in result.stdout

    @patch("fessctl.commands.scheduler.FessAPIClient")
    def test_start_without_job_log_id_text_output(self, mock_client_class, runner):
        """Test backward compatibility: no jobLogId field (old Fess)."""
        mock_client = Mock()
        mock_client.start_scheduler.return_value = {
            "response": {"status": 0}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(scheduler_app, ["start", "sched-001"])
        assert result.exit_code == 0
        assert "started successfully" in result.stdout
        assert "Job Log ID" not in result.stdout

    @patch("fessctl.commands.scheduler.FessAPIClient")
    def test_start_with_null_job_log_id_text_output(self, mock_client_class, runner):
        """Test that null jobLogId (logging disabled) does not show ID."""
        mock_client = Mock()
        mock_client.start_scheduler.return_value = {
            "response": {"status": 0, "jobLogId": None}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(scheduler_app, ["start", "sched-001"])
        assert result.exit_code == 0
        assert "started successfully" in result.stdout
        assert "Job Log ID" not in result.stdout

    @patch("fessctl.commands.scheduler.FessAPIClient")
    def test_start_with_job_log_id_json_output(self, mock_client_class, runner):
        """Test that jobLogId appears in JSON output."""
        mock_client = Mock()
        mock_client.start_scheduler.return_value = {
            "response": {"status": 0, "jobLogId": "abc123def456"}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(scheduler_app, ["start", "sched-001", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["response"]["jobLogId"] == "abc123def456"

    @patch("fessctl.commands.scheduler.FessAPIClient")
    def test_start_failure_text_output(self, mock_client_class, runner):
        """Test that failure response does not show jobLogId."""
        mock_client = Mock()
        mock_client.start_scheduler.return_value = {
            "response": {"status": 1, "message": "Job is not available"}
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(scheduler_app, ["start", "sched-001"])
        assert result.exit_code != 0
        assert "Failed to start Scheduler" in result.stdout
        assert "Job Log ID" not in result.stdout
