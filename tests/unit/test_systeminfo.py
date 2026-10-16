"""
Unit tests for the systeminfo command.
"""
import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClientError
from fessctl.commands.systeminfo import systeminfo_app

RESPONSE = {"response": {
    "status": 0,
    "bug_report_props": [{"label": "os.name", "value": "Linux"}],
    "env_props": [{"label": "FESS_PORT", "value": "8080"}],
    "fess_props": [{"label": "domain.title", "value": "Fess"}],
    "system_props": [{"label": "java.specification.version", "value": "21"}],
}}


@pytest.fixture
def runner():
    return CliRunner()


@patch("fessctl.commands.systeminfo.FessAPIClient")
def test_text_output_lists_each_group(mock_client_class, runner):
    mock_client_class.return_value.get_systeminfo.return_value = RESPONSE

    result = runner.invoke(systeminfo_app, [])

    assert result.exit_code == 0
    for line in ("## Bug Report", "| os.name | Linux |", "## Environment", "| FESS_PORT | 8080 |",
                 "## Fess", "| domain.title | Fess |", "## System", "| java.specification.version | 21 |"):
        assert line in result.stdout


@patch("fessctl.commands.systeminfo.FessAPIClient")
def test_json_output_is_the_response(mock_client_class, runner):
    mock_client_class.return_value.get_systeminfo.return_value = RESPONSE

    result = runner.invoke(systeminfo_app, ["--output", "json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == RESPONSE


@patch("fessctl.commands.systeminfo.FessAPIClient")
def test_failure_exits_with_status(mock_client_class, runner):
    mock_client_class.return_value.get_systeminfo.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}

    result = runner.invoke(systeminfo_app, [])

    assert result.exit_code == 3
    assert "Unauthorized request." in result.stdout


@patch("fessctl.commands.systeminfo.FessAPIClient")
def test_failure_exits_non_zero_in_json_mode(mock_client_class, runner):
    mock_client_class.return_value.get_systeminfo.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}

    result = runner.invoke(systeminfo_app, ["-o", "json"])

    assert result.exit_code == 3


@patch("fessctl.commands.systeminfo.FessAPIClient")
def test_client_error_exits_1(mock_client_class, runner):
    mock_client_class.return_value.get_systeminfo.side_effect = FessAPIClientError(-1, "Network error: refused")

    result = runner.invoke(systeminfo_app, [])

    assert result.exit_code == 1
    assert "Network error: refused" in result.stdout
