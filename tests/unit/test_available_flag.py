"""
--available/--no-available on the commands that create or update an enableable resource.
A bare --available flag could only ever send true, so a config could not be created or switched off.
"""
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from fessctl.commands.dataconfig import dataconfig_app
from fessctl.commands.fileconfig import fileconfig_app
from fessctl.commands.scheduler import scheduler_app
from fessctl.commands.webconfig import webconfig_app

runner = CliRunner()

CREATE = [
    ("webconfig", webconfig_app, ["--name", "n", "--url", "http://a.example.com/"], "create_webconfig"),
    ("fileconfig", fileconfig_app, ["--name", "n", "--path", "file:/tmp/a/"], "create_fileconfig"),
    ("dataconfig", dataconfig_app, ["--name", "n", "--handler-name", "CsvDataStore"], "create_dataconfig"),
    ("scheduler", scheduler_app, ["--name", "n", "--target", "all", "--script-type", "groovy"], "create_scheduler"),
]
UPDATE = [
    ("webconfig", webconfig_app, "update_webconfig", "get_webconfig"),
    ("fileconfig", fileconfig_app, "update_fileconfig", "get_fileconfig"),
    ("dataconfig", dataconfig_app, "update_dataconfig", "get_dataconfig"),
    ("scheduler", scheduler_app, "update_scheduler", "get_scheduler"),
]


def _truthy(value):
    return value is True or value == "true"


@pytest.mark.parametrize("module,app,args,method", CREATE, ids=[c[0] for c in CREATE])
@pytest.mark.parametrize("flags,expected", [([], True), (["--available"], True), (["--no-available"], False)])
def test_create_sends_the_requested_availability(module, app, args, method, flags, expected):
    with patch(f"fessctl.commands.{module}.FessAPIClient") as client_class:
        client = Mock()
        getattr(client, method).return_value = {"response": {"status": 0, "id": "x"}}
        client_class.return_value = client
        result = runner.invoke(app, ["create", *args, *flags])
        assert result.exit_code == 0, result.stdout
        sent = getattr(client, method).call_args[0][0]
        assert _truthy(sent["available"]) is expected


@pytest.mark.parametrize("module,app,update,get", UPDATE, ids=[u[0] for u in UPDATE])
@pytest.mark.parametrize(
    "flags,stored,expected",
    [
        (["--available"], "false", True),
        (["--no-available"], "true", False),
        ([], "false", False),  # omitted: the stored value is kept
        ([], "true", True),
    ],
)
def test_update_sends_the_requested_availability(module, app, update, get, flags, stored, expected):
    with patch(f"fessctl.commands.{module}.FessAPIClient") as client_class:
        client = Mock()
        getattr(client, get).return_value = {"response": {"status": 0, "setting": {"id": "x", "name": "n", "available": stored}}}
        getattr(client, update).return_value = {"response": {"status": 0, "id": "x"}}
        client_class.return_value = client
        result = runner.invoke(app, ["update", "x", "--sort-order", "3", *flags])
        assert result.exit_code == 0, result.stdout
        sent = getattr(client, update).call_args[0][0]
        assert _truthy(sent["available"]) is expected
