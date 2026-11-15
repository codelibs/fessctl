"""
Unit tests for the crawlinginfo progress and delete-all commands.
"""
import json
from unittest.mock import Mock, patch

import pytest
import yaml
from typer.testing import CliRunner

from fessctl.api.client import FessAPIClient
from fessctl.commands.crawlinginfo import crawlinginfo_app
from fessctl.config.settings import Settings

PROGRESS = {"response": {"status": 0, "total": 2, "progress": [
    {"config_id": "Wabc", "name": "Example Site", "count": 4200, "last_count": 10000,
     "updated_time": 1792149753263, "percent": 42},
    # percent is left out when there is no previous completed crawl
    {"config_id": "Ddef", "name": "Example | DB", "count": 15, "last_count": 0,
     "updated_time": 1792149753263},
]}}


def make_client(version: str = "15.10.0") -> FessAPIClient:
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://localhost:8080"
    settings.access_token = "test-token"
    settings.fess_version = version
    return FessAPIClient(settings)


def ok_response():
    response = Mock()
    response.json.return_value = {"response": {"status": 0}}
    return response


class TestClient:
    def test_progress_gets_the_progress_endpoint(self):
        with patch("httpx.get", return_value=ok_response()) as get:
            make_client().get_crawlinginfo_progress()
        assert get.call_args[0][0] == "http://localhost:8080/api/admin/crawlinginfo/progress"
        assert get.call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @pytest.mark.parametrize("version", ["15.10.0", "15.9.0", "14.19.2"])
    def test_delete_all_deletes_the_all_endpoint(self, version):
        with patch("httpx.delete", return_value=ok_response()) as delete:
            make_client(version).delete_all_crawlinginfos()
        assert delete.call_args[0][0] == "http://localhost:8080/api/admin/crawlinginfo/all"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def client():
    with patch("fessctl.commands.crawlinginfo.FessAPIClient") as client_class:
        yield client_class.return_value


class TestProgress:
    def test_text_output_is_a_table(self, client, runner):
        client.get_crawlinginfo_progress.return_value = PROGRESS
        result = runner.invoke(crawlinginfo_app, ["progress"])
        assert result.exit_code == 0
        assert "| NAME | CONFIG ID | COUNT | LAST COUNT | PERCENT | UPDATED TIME |" in result.stdout
        assert "| Example Site | Wabc | 4200 | 10000 | 42% | 2026-10-16T11:22:33Z |" in result.stdout
        # a crawl without a previous count shows no percentage
        assert "| Example \\| DB | Ddef | 15 | 0 | - | 2026-10-16T11:22:33Z |" in result.stdout

    def test_no_running_crawl(self, client, runner):
        client.get_crawlinginfo_progress.return_value = {"response": {"status": 0, "progress": [], "total": 0}}
        result = runner.invoke(crawlinginfo_app, ["progress"])
        assert result.exit_code == 0
        assert "No running crawls found." in result.stdout

    def test_json_and_yaml_print_the_whole_response(self, client, runner):
        client.get_crawlinginfo_progress.return_value = PROGRESS
        as_json = runner.invoke(crawlinginfo_app, ["progress", "-o", "json"])
        assert json.loads(as_json.stdout) == PROGRESS
        as_yaml = runner.invoke(crawlinginfo_app, ["progress", "-o", "yaml"])
        assert yaml.safe_load(as_yaml.stdout) == PROGRESS

    @pytest.mark.parametrize("output", ["text", "json", "yaml"])
    def test_failure_exits_with_status_in_every_format(self, client, runner, output):
        client.get_crawlinginfo_progress.return_value = {"response": {"status": 3, "message": "Unauthorized request."}}
        result = runner.invoke(crawlinginfo_app, ["progress", "-o", output])
        assert result.exit_code == 3
        assert "Unauthorized request." in result.stdout


class TestDeleteAll:
    def test_aborts_without_confirmation(self, client, runner):
        result = runner.invoke(crawlinginfo_app, ["delete-all"], input="n\n")
        assert result.exit_code != 0
        assert "except the running ones" in result.stdout
        client.delete_all_crawlinginfos.assert_not_called()

    def test_confirmed_deletes(self, client, runner):
        client.delete_all_crawlinginfos.return_value = {"response": {"status": 0}}
        result = runner.invoke(crawlinginfo_app, ["delete-all"], input="y\n")
        assert result.exit_code == 0
        client.delete_all_crawlinginfos.assert_called_once_with()

    def test_yes_skips_the_prompt(self, client, runner):
        client.delete_all_crawlinginfos.return_value = {"response": {"status": 0}}
        result = runner.invoke(crawlinginfo_app, ["delete-all", "--yes"])
        assert result.exit_code == 0
        assert "deleted successfully" in result.stdout

    @pytest.mark.parametrize("output", ["text", "json", "yaml"])
    def test_failure_exits_with_status_in_every_format(self, client, runner, output):
        client.delete_all_crawlinginfos.return_value = {"response": {"status": 1, "message": "boom"}}
        result = runner.invoke(crawlinginfo_app, ["delete-all", "-y", "-o", output])
        assert result.exit_code == 1
        assert "boom" in result.stdout

    def test_json_prints_the_raw_response(self, client, runner):
        client.delete_all_crawlinginfos.return_value = {"response": {"status": 0}}
        result = runner.invoke(crawlinginfo_app, ["delete-all", "-y", "-o", "json"])
        assert json.loads(result.stdout) == {"response": {"status": 0}}
