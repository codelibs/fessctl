"""
Unit tests for the stats command.
"""
import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.stats import flatten, stats_app

RESPONSE = {"response": {"status": 0, "stats": {
    "jvm": {
        "memory": {"heap": {"used": 10, "max": 20}},
        "gc": [{"key": "young", "count": 3, "time": 7}],
    },
    "os": {"load_averages": [0.5, 0.25]},
    "fs": [{"path": "/", "free": 1, "total": 2}],
}}}


@pytest.fixture
def runner():
    return CliRunner()


def test_flatten_names_rows_by_path_and_list_item_key():
    rows = flatten(RESPONSE["response"]["stats"])

    assert {r["name"]: r["value"] for r in rows} == {
        "jvm.memory.heap.used": 10,
        "jvm.memory.heap.max": 20,
        "jvm.gc[young].count": 3,
        "jvm.gc[young].time": 7,
        "os.load_averages[0]": 0.5,
        "os.load_averages[1]": 0.25,
        "fs[/].free": 1,
        "fs[/].total": 2,
    }


@patch("fessctl.commands.stats.FessAPIClient")
def test_text_output(mock_client_class, runner):
    mock_client_class.return_value.get_stats.return_value = RESPONSE

    result = runner.invoke(stats_app, [])

    assert result.exit_code == 0
    assert "| jvm.memory.heap.used | 10 |" in result.stdout
    assert "| fs[/].free | 1 |" in result.stdout


@patch("fessctl.commands.stats.FessAPIClient")
def test_json_output_is_the_response(mock_client_class, runner):
    mock_client_class.return_value.get_stats.return_value = RESPONSE

    result = runner.invoke(stats_app, ["-o", "json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == RESPONSE


@patch("fessctl.commands.stats.FessAPIClient")
def test_failure_exits_with_status(mock_client_class, runner):
    mock_client_class.return_value.get_stats.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}

    result = runner.invoke(stats_app, [])

    assert result.exit_code == 3
    assert "Unauthorized request." in result.stdout
