import inspect
import json
from pathlib import Path
from typing import List, NamedTuple, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient, FessAPIClientError
from fessctl.config.settings import Settings
from fessctl.utils import (
    format_detail_markdown,
    format_list_markdown,
    format_result_markdown,
)

dict_app = typer.Typer()


class Field(NamedTuple):
    api: str  # field name in the API
    option: str  # CLI option name (without the leading dashes)
    help: str
    multi: bool = False  # one value per line in the API; the option is repeatable


# The entry fields of each dictionary type, as the admin API defines them. The
# type names are the `type` values of `dict list` and the URL path segments.
DICT_FIELDS = {
    "synonym": [
        Field("inputs", "source", "Source word; repeat for several (no commas or '=>')", True),
        Field("outputs", "target", "Target word; repeat for several (no commas or '=>')", True),
    ],
    "mapping": [
        Field("inputs", "source", "Source character or string; repeat for several", True),
        Field("output", "target", "Replacement string"),
    ],
    "kuromoji": [
        Field("token", "token", "Token"),
        Field("segmentation", "segmentation", "Segmentation, words separated by spaces"),
        Field("reading", "reading", "Reading, one per segment separated by spaces"),
        Field("pos", "pos", "Part-of-speech"),
    ],
    "stopwords": [Field("input", "word", "Stop word")],
    "protwords": [Field("input", "word", "Protected word")],
    "stemmeroverride": [
        Field("input", "source", "Source word"),
        Field("output", "target", "Stemmed form"),
    ],
}

OUTPUT_HELP = "Output format (text, json, yaml)"


def _status(result: dict) -> int:
    return result.get("response", {}).get("status", 1)


def _message(result: dict) -> str:
    return result.get("response", {}).get("message", "")


def _emit(result: dict, output: str, ok_message: str, fail_message: str,
          dict_type: str, action: str, resource_id: str = "") -> None:
    """Prints the outcome of a write command; exits non-zero when the API failed."""
    status = _status(result)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    elif status == 0:
        typer.echo(format_result_markdown(True, ok_message, f"Dict.{dict_type}", action, resource_id))
    else:
        typer.echo(format_result_markdown(
            False, f"{fail_message} {_message(result)} Status code: {status}", f"Dict.{dict_type}", action))
    if status != 0:
        raise typer.Exit(code=status)


def _param(name: str, annotation, default) -> inspect.Parameter:
    return inspect.Parameter(
        name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=annotation)


def _output_param() -> inspect.Parameter:
    return _param("output", str, typer.Option("text", "--output", "-o", help=OUTPUT_HELP))


def _dict_id_param() -> inspect.Parameter:
    return _param("dict_id", str, typer.Argument(..., help="Dictionary ID (see `dict list`)"))


def _item_id_param() -> inspect.Parameter:
    return _param("item_id", int, typer.Argument(..., help="Entry ID"))


def _field_param(field: Field, required: bool) -> inspect.Parameter:
    annotation = List[str] if field.multi else str
    if not required:
        annotation = Optional[annotation]
    return _param(field.option.replace("-", "_"), annotation,
                  typer.Option(... if required else None, f"--{field.option}", help=field.help))


def _command(app: typer.Typer, name: str, func, params: list, doc: str) -> None:
    """Registers func as a command whose Typer options are given by params.

    The options of create and update differ per dictionary type, so their
    signatures are built from DICT_FIELDS instead of being written six times.
    """
    func.__signature__ = inspect.Signature(params)
    func.__annotations__ = {p.name: p.annotation for p in params}
    func.__doc__ = doc
    app.command(name)(func)


def _api_value(field: Field, value):
    return "\n".join(value) if field.multi else value


def _register_type(dict_type: str) -> None:
    fields = DICT_FIELDS[dict_type]
    columns = [("ID", "id")] + [(f.api.upper(), f.api) for f in fields]
    type_app = typer.Typer()

    def create(**kwargs):
        for f in fields:
            # Required options are not always enforced by Click, and Fess accepts a
            # mapping without a target (reporting success but storing nothing).
            if not kwargs[f.option.replace("-", "_")]:
                raise typer.BadParameter("This option is required.", param_hint=f"--{f.option}")
        client = FessAPIClient(Settings())
        config = {f.api: _api_value(f, kwargs[f.option.replace("-", "_")]) for f in fields}
        result = client.create_dict_item(dict_type, kwargs["dict_id"], config)
        # Fess before 15.9 reports the ID of a new entry as "0"; `list` shows the real one.
        item_id = result.get("response", {}).get("id", "")
        if item_id == "0":
            item_id = ""
        _emit(result, kwargs["output"],
              f"{dict_type} entry {f'{item_id!r} ' if item_id else ''}created successfully.",
              f"Failed to create {dict_type} entry.", dict_type, "create", item_id)

    _command(type_app, "create", create,
             [_dict_id_param()] + [_field_param(f, True) for f in fields] + [_output_param()],
             f"Create an entry in a {dict_type} dictionary.")

    def update(**kwargs):
        client = FessAPIClient(Settings())
        dict_id, item_id = kwargs["dict_id"], kwargs["item_id"]
        current = client.get_dict_item(dict_type, dict_id, item_id)
        if _status(current) != 0:
            typer.echo(format_result_markdown(
                False, f"{dict_type} entry '{item_id}' not found. {_message(current)}",
                f"Dict.{dict_type}", "update"))
            raise typer.Exit(code=1)

        # The PUT replaces the whole entry, so start from the current one and
        # override only the given fields.
        config = current["response"]["setting"]
        for f in fields:
            value = kwargs[f.option.replace("-", "_")]
            if value is not None:
                config[f.api] = _api_value(f, value)
        result = client.update_dict_item(dict_type, dict_id, config)
        _emit(result, kwargs["output"], f"{dict_type} entry '{item_id}' updated successfully.",
              f"Failed to update {dict_type} entry.", dict_type, "update", str(item_id))

    _command(type_app, "update", update,
             [_dict_id_param(), _item_id_param()] + [_field_param(f, False) for f in fields] + [_output_param()],
             f"Update an entry of a {dict_type} dictionary; unspecified fields are kept.")

    def delete(**kwargs):
        client = FessAPIClient(Settings())
        result = client.delete_dict_item(dict_type, kwargs["dict_id"], kwargs["item_id"])
        _emit(result, kwargs["output"], f"{dict_type} entry '{kwargs['item_id']}' deleted successfully.",
              f"Failed to delete {dict_type} entry.", dict_type, "delete", str(kwargs["item_id"]))

    _command(type_app, "delete", delete, [_dict_id_param(), _item_id_param(), _output_param()],
             f"Delete an entry of a {dict_type} dictionary by ID.")

    def get(**kwargs):
        client = FessAPIClient(Settings())
        result = client.get_dict_item(dict_type, kwargs["dict_id"], kwargs["item_id"])
        status = _status(result)
        output = kwargs["output"]
        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            setting = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"{dict_type} entry: {setting.get('id', '-')}", setting, [("id", "id")] + [(f.api, f.api) for f in fields]))
        else:
            typer.echo(format_result_markdown(
                False, f"Failed to retrieve {dict_type} entry. {_message(result)} Status code: {status}",
                f"Dict.{dict_type}", "get"))
        if status != 0:
            raise typer.Exit(code=status)

    _command(type_app, "get", get, [_dict_id_param(), _item_id_param(), _output_param()],
             f"Retrieve an entry of a {dict_type} dictionary by ID.")

    def list_items(**kwargs):
        client = FessAPIClient(Settings())
        result = client.list_dict_items(dict_type, kwargs["dict_id"], page=kwargs["page"], size=kwargs["size"])
        status = _status(result)
        output = kwargs["output"]
        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            items = result.get("response", {}).get("settings", [])
            if not items:
                typer.echo(f"No {dict_type} entries found.")
            else:
                typer.echo(format_list_markdown(f"{dict_type} entries", items, columns))
        else:
            typer.echo(format_result_markdown(
                False, f"Failed to list {dict_type} entries. {_message(result)} Status code: {status}",
                f"Dict.{dict_type}", "list"))
        if status != 0:
            raise typer.Exit(code=status)

    _command(type_app, "list", list_items,
             [_dict_id_param(),
              _param("page", int, typer.Option(1, "--page", "-p", help="Page number")),
              _param("size", int, typer.Option(100, "--size", "-s", help="Page size")),
              _output_param()],
             f"List the entries of a {dict_type} dictionary. An unknown dictionary ID lists nothing.")

    def upload(**kwargs):
        file: Path = kwargs["file"]
        output = kwargs["output"]
        if not file.is_file():
            typer.echo(format_result_markdown(
                False, f"File '{file}' not found.", f"Dict.{dict_type}", "upload"))
            raise typer.Exit(code=1)
        if not kwargs["yes"]:
            typer.confirm(
                f"Replace the whole dictionary '{kwargs['dict_id']}' with '{file}'?", abort=True)
        client = FessAPIClient(Settings())
        result = client.upload_dict(dict_type, kwargs["dict_id"], str(file))
        _emit(result, output, f"{dict_type} dictionary '{kwargs['dict_id']}' replaced successfully.",
              f"Failed to upload {dict_type} dictionary.", dict_type, "upload", kwargs["dict_id"])

    _command(type_app, "upload", upload,
             [_dict_id_param(),
              _param("file", Path, typer.Argument(..., help="Local file that replaces the dictionary")),
              _param("yes", bool, typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt")),
              _output_param()],
             f"Replace a whole {dict_type} dictionary file with a local file "
             "(requires Fess 14.x or 15.9+; Fess 15.6 to 15.8 cannot receive uploads).")

    def download(**kwargs):
        file: Optional[Path] = kwargs["file"]
        client = FessAPIClient(Settings())
        try:
            content = client.download_dict(dict_type, kwargs["dict_id"])
        except FessAPIClientError as e:
            _emit({"response": {"status": 1, "message": e.content}}, kwargs["output"], "",
                  f"Failed to download {dict_type} dictionary.", dict_type, "download")
            return
        if file is None:
            typer.echo(content, nl=False)
            return
        if file.exists() and not kwargs["force"]:
            typer.echo(format_result_markdown(
                False, f"File '{file}' already exists. Use --force to overwrite it.",
                f"Dict.{dict_type}", "download"))
            raise typer.Exit(code=1)
        file.write_bytes(content)
        _emit({"response": {"status": 0}}, kwargs["output"],
              f"{dict_type} dictionary '{kwargs['dict_id']}' saved to '{file}' ({len(content)} bytes).",
              "", dict_type, "download", kwargs["dict_id"])

    _command(type_app, "download", download,
             [_dict_id_param(),
              _param("file", Optional[Path], typer.Option(
                  None, "--file", "-f", help="Write to this file instead of standard output")),
              _param("force", bool, typer.Option(False, "--force", help="Overwrite --file if it exists")),
              _output_param()],
             f"Download a {dict_type} dictionary file to standard output or to --file.")

    dict_app.add_typer(type_app, name=dict_type,
                       help=f"Manage {dict_type} dictionaries: " + ", ".join(f"--{f.option}" for f in fields) + ".")


@dict_app.command("list")
def list_dicts(
    dict_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Only this type (synonym, mapping, kuromoji, stopwords, protwords, stemmeroverride)"),
    output: str = typer.Option(
        "text", "--output", "-o", help=OUTPUT_HELP),
):
    """
    List the dictionary files; use their ID with the per-type subcommands.
    """
    client = FessAPIClient(Settings())
    result = client.get_dicts()
    status = _status(result)
    response = result.get("response", {})
    if dict_type is not None and status == 0:
        response["settings"] = [d for d in response.get("settings", []) if d.get("type") == dict_type]
        if "total" in response:
            response["total"] = len(response["settings"])

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    elif status == 0:
        dicts = response.get("settings", [])
        if not dicts:
            typer.echo("No Dictionaries found.")
        else:
            typer.echo(format_list_markdown("Dictionaries", dicts, [
                ("TYPE", "type"), ("ID", "id"), ("PATH", "path"), ("TIMESTAMP", "timestamp"),
            ]))
    else:
        typer.echo(format_result_markdown(
            False, f"Failed to list Dictionaries. {_message(result)} Status code: {status}", "Dict", "list"))
    if status != 0:
        raise typer.Exit(code=status)


for _dict_type in DICT_FIELDS:
    _register_type(_dict_type)
