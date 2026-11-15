"""
Every subcommand must exit with the API status code when the Fess API reports
a failure, whatever the --output format (text, json or yaml).
"""
import importlib
import json
from unittest.mock import patch

import pytest
import typer
import yaml
from typer.testing import CliRunner

MODULES = [
    "accesstoken", "badword", "boostdoc", "crawlinginfo", "dataconfig",
    "duplicatehost", "elevateword", "failureurl", "fileauth", "fileconfig",
    "group", "joblog", "keymatch", "labeltype", "pathmap", "relatedcontent",
    "relatedquery", "reqheader", "role", "scheduler", "tagtype", "user",
    "webauth", "webconfig", "theme",
]


# File transfers need a real file or return bytes; tests/unit/test_csv_transfer.py covers their exit codes.
FILE_TRANSFERS = {("badword", "upload"), ("badword", "download"),
                  ("elevateword", "upload"), ("elevateword", "download")}


def _commands():
    cases = []
    for module in MODULES:
        app = getattr(importlib.import_module(f"fessctl.commands.{module}"), f"{module}_app")
        for name, command in typer.main.get_command(app).commands.items():
            if (module, name) in FILE_TRANSFERS:
                continue
            args = [name] + (["--yes"] if name == "delete-all" else [])
            for param in command.params:
                if not param.required:
                    continue
                # "1" satisfies string, int and float parameters alike.
                args += [param.opts[0], "1"] if param.param_type_name == "option" else ["1"]
            cases.append(pytest.param(module, name, args, id=f"{module}-{name}"))
    return cases


class FakeClient:
    """Fails every call with `status`; `get_*` succeeds when a command reads before it writes."""

    def __init__(self, status, prefetch_ok):
        self.status = status
        self.prefetch_ok = prefetch_ok

    def __getattr__(self, name):
        def call(*args, **kwargs):
            if self.prefetch_ok and name.startswith("get_"):
                return {"response": {"status": 0, "setting": {}}}
            return {"response": {"status": self.status, "message": "boom"}}
        return call


@pytest.mark.parametrize("module,name,args", _commands())
@pytest.mark.parametrize("status", [1, 3])
@pytest.mark.parametrize("output", ["text", "json", "yaml"])
def test_failure_exits_with_status(module, name, args, status, output):
    prefetch_ok = name == "update"
    with patch(f"fessctl.commands.{module}.FessAPIClient",
               return_value=FakeClient(status, prefetch_ok)):
        app = getattr(importlib.import_module(f"fessctl.commands.{module}"), f"{module}_app")
        result = CliRunner().invoke(app, args + ["--output", output])
    assert result.exit_code == status, result.output
    if output == "json":
        assert json.loads(result.stdout)["response"]["status"] == status
    elif output == "yaml":
        assert yaml.safe_load(result.stdout)["response"]["status"] == status


@pytest.mark.parametrize("module,name,args", _commands())
@pytest.mark.parametrize("output", ["text", "json", "yaml"])
def test_success_exits_zero(module, name, args, output):
    # Only used to check that the checks above are not vacuous: success must stay 0.
    class OkClient:
        def __getattr__(self, _):
            return lambda *a, **k: {"response": {"status": 0, "setting": {}, "settings": [], "id": "1"}}

    with patch(f"fessctl.commands.{module}.FessAPIClient", return_value=OkClient()):
        app = getattr(importlib.import_module(f"fessctl.commands.{module}"), f"{module}_app")
        result = CliRunner().invoke(app, args + ["--output", output])
    assert result.exit_code == 0, result.output
