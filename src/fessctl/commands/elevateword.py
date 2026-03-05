import datetime
import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import (
    format_detail_markdown,
    format_list_markdown,
    format_result_markdown,
    to_utc_iso8601,
)

elevateword_app = typer.Typer()


@elevateword_app.command("create")
def create_elevateword(
    suggest_word: str = typer.Option(...,
                                     "--suggest-word", help="Suggest word"),
    boost: float = typer.Option(..., "--boost", help="Boost value"),
    version_no: int = typer.Option(..., "--version-no", help="Version number"),
    label_type_ids: List[str] = typer.Option(
        [], "--label-type-id", help="Label type IDs"),
    reading: Optional[str] = typer.Option(
        None, "--reading", help="Reading of the word"),
    target_label: Optional[str] = typer.Option(
        None, "--target-label", help="Target label"),
    permissions: List[str] = typer.Option(
        [], "--permission", help="Permissions"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time", help="Created time in milliseconds (UTC)"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new ElevateWord.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "suggest_word": suggest_word,
        "boost": boost,
        "version_no": version_no,
        "label_type_ids": label_type_ids,
        "created_by": created_by,
        "created_time": created_time,
    }

    if reading:
        config["reading"] = reading
    if target_label:
        config["target_label"] = target_label
    if permissions:
        config["permissions"] = "\n".join(permissions)

    result = client.create_elevateword(config)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            eid = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"ElevateWord '{eid}' created successfully.", "ElevateWord", "create", eid))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create ElevateWord. {message} Status code: {status}", "ElevateWord", "create"))
            raise typer.Exit(code=status)


@elevateword_app.command("update")
def update_elevateword(
    config_id: str = typer.Argument(..., help="ElevateWord ID"),
    suggest_word: Optional[str] = typer.Option(
        None, "--suggest-word", help="Suggest word"),
    boost: Optional[float] = typer.Option(None, "--boost", help="Boost value"),
    version_no: Optional[int] = typer.Option(
        None, "--version-no", help="Version number"),
    label_type_ids: Optional[List[str]] = typer.Option(
        None, "--label-type-id", help="Label type IDs"),
    reading: Optional[str] = typer.Option(
        None, "--reading", help="Reading of the word"),
    target_label: Optional[str] = typer.Option(
        None, "--target-label", help="Target label"),
    permissions: Optional[List[str]] = typer.Option(
        None, "--permission", help="Permissions"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time", help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Update an existing ElevateWord.
    """
    client = FessAPIClient(Settings())
    result = client.get_elevateword(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"ElevateWord with ID '{config_id}' not found. {message}", "ElevateWord", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if suggest_word is not None:
        config["suggest_word"] = suggest_word
    if boost is not None:
        config["boost"] = boost
    if version_no is not None:
        config["version_no"] = version_no
    if label_type_ids is not None:
        config["label_type_ids"] = label_type_ids
    if reading is not None:
        config["reading"] = reading
    if target_label is not None:
        config["target_label"] = target_label
    if permissions is not None:
        config["permissions"] = "\n".join(permissions)

    result = client.update_elevateword(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"ElevateWord '{config_id}' updated successfully.", "ElevateWord", "update", config_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update ElevateWord. {message} Status code: {status}", "ElevateWord", "update"))
            raise typer.Exit(code=status)


@elevateword_app.command("delete")
def delete_elevateword(
    config_id: str = typer.Argument(..., help="ElevateWord ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete an ElevateWord by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_elevateword(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"ElevateWord '{config_id}' deleted successfully.", "ElevateWord", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete ElevateWord. {message} Status code: {status}", "ElevateWord", "delete"))
            raise typer.Exit(code=status)


@elevateword_app.command("get")
def get_elevateword(
    config_id: str = typer.Argument(..., help="ElevateWord ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve an ElevateWord by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_elevateword(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            elevateword = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"ElevateWord Details: {elevateword.get('id', '-')}",
                elevateword,
                [
                    ("id", "id"),
                    ("suggest_word", "suggest_word"),
                    ("boost", "boost"),
                    ("version_no", "version_no"),
                    ("label_type_ids", "label_type_ids"),
                    ("reading", "reading"),
                    ("target_label", "target_label"),
                    ("permissions", "permissions"),
                    ("crud_mode", "crud_mode"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                ],
                transforms={"created_time": to_utc_iso8601, "updated_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve ElevateWord. {message} Status code: {status}", "ElevateWord", "get"))
            raise typer.Exit(code=1)


@elevateword_app.command("list")
def list_elevatewords(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List ElevateWords.
    """
    client = FessAPIClient(Settings())
    result = client.list_elevatewords(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            elevatewords = result.get("response", {}).get("settings", [])
            if not elevatewords:
                typer.echo("No ElevateWords found.")
            else:
                display_items = []
                for ew in elevatewords:
                    d = dict(ew)
                    d["updated_time_display"] = to_utc_iso8601(ew.get("updated_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("ElevateWords", display_items, [
                    ("ID", "id"), ("SUGGEST WORD", "suggest_word"),
                    ("BOOST", "boost"), ("VERSION NO", "version_no"),
                    ("UPDATED BY", "updated_by"), ("UPDATED TIME", "updated_time_display"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list ElevateWords. {message} Status code: {status}", "ElevateWord", "list"))
            raise typer.Exit(code=status)
