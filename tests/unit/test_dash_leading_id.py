"""
Fess IDs are URL-safe Base64, so an ID can start with '-'. The parser reads such an ID as an
option unless it follows '--'; every ID argument says so in --help, and the '--' form must pass
the ID to the API unchanged.
"""
from unittest.mock import Mock, patch

import click
import pytest
import typer
from typer.testing import CliRunner

from fessctl.cli import app

DASH_ID = "-abcDEF"


def _leaf_commands(command, path):
    if isinstance(command, click.Group):
        for name, sub in command.commands.items():
            yield from _leaf_commands(sub, path + [name])
    else:
        yield path, command


def _id_commands():
    cases = []
    for path, command in _leaf_commands(typer.main.get_command(app), []):
        id_params = [p for p in command.params
                     if p.param_type_name == "argument" and p.name.endswith("_id")
                     and p.type is click.STRING]
        if id_params:
            cases.append(pytest.param(path, command, id=" ".join(path)))
    return cases


ID_COMMANDS = _id_commands()


def test_id_commands_are_found():
    # Guards the parametrized tests below against an empty (vacuously green) case list.
    assert len(ID_COMMANDS) >= 80


@pytest.mark.parametrize("path,command", ID_COMMANDS)
def test_help_explains_dash_leading_id(path, command):
    result = CliRunner().invoke(app, path + ["--help"])
    assert result.exit_code == 0, result.output
    assert "'--'" in result.output


@pytest.mark.parametrize("path,command", ID_COMMANDS)
def test_dash_leading_id_after_double_dash_is_parsed(path, command):
    options, positionals, id_names = [], [], []
    for param in command.params:
        if param.param_type_name == "argument":
            if param.name.endswith("_id") and param.type is click.STRING:
                positionals.append(DASH_ID)
                id_names.append(param.name)
            else:
                positionals.append("1")
        elif param.required:
            options += [param.opts[0], "1"]

    # resilient_parsing: only the parsing matters here, not e.g. whether a file option exists.
    ctx = command.make_context(path[-1], options + ["--"] + positionals, resilient_parsing=True)

    for name in id_names:
        assert ctx.params[name] == DASH_ID


@patch("fessctl.commands.keymatch.FessAPIClient")
def test_keymatch_update_sends_dash_leading_id(mock_client_class):
    client = Mock()
    client.get_keymatch.return_value = {"response": {"status": 0, "setting": {"id": DASH_ID, "max_size": 10}}}
    client.update_keymatch.return_value = {"response": {"status": 0, "id": DASH_ID}}
    mock_client_class.return_value = client

    result = CliRunner().invoke(app, ["keymatch", "update", "--max-size", "3", "--", DASH_ID])

    assert result.exit_code == 0, result.output
    client.get_keymatch.assert_called_once_with(DASH_ID)
    sent = client.update_keymatch.call_args.args[0]
    assert sent["id"] == DASH_ID
    assert sent["max_size"] == 3


def test_dash_leading_id_without_double_dash_is_an_option():
    # Pins the parser behaviour the help text describes.
    result = CliRunner().invoke(app, ["keymatch", "get", DASH_ID])
    assert result.exit_code == 2
    assert "No such option" in result.output
