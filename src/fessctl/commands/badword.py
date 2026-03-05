import datetime
import json
from typing import Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

badword_app = typer.Typer()


@badword_app.command("create")
def create_badword(
    suggest_word: str = typer.Option(..., "--suggest-word",
                                     help="Suggested word (no whitespace allowed)"),
    created_by: str = typer.Option(
        "admin", "--created-by", help="Creator's name"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new BadWord.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "suggest_word": suggest_word,
        "created_by": created_by,
        "created_time": created_time,
    }

    result = client.create_badword(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            badword_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"BadWord '{badword_id}' created successfully.", "BadWord", "create", badword_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create BadWord. {message} Status code: {status}", "BadWord", "create"))
            raise typer.Exit(code=status)


@badword_app.command("update")
def update_badword(
    config_id: str = typer.Argument(..., help="BadWord ID"),
    suggest_word: Optional[str] = typer.Option(
        None, "--suggest-word", help="Suggested word"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Update an existing BadWord.
    """
    client = FessAPIClient(Settings())
    result = client.get_badword(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"BadWord with ID '{config_id}' not found. {message}", "BadWord", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if suggest_word is not None:
        config["suggest_word"] = suggest_word

    result = client.update_badword(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"BadWord '{config_id}' updated successfully.", "BadWord", "update", config_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update BadWord. {message} Status code: {status}", "BadWord", "update"))
            raise typer.Exit(code=status)


@badword_app.command("delete")
def delete_badword(
    config_id: str = typer.Argument(..., help="BadWord ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a BadWord by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_badword(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"BadWord '{config_id}' deleted successfully.", "BadWord", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete BadWord. {message} Status code: {status}", "BadWord", "delete"))
            raise typer.Exit(code=status)


@badword_app.command("get")
def get_badword(
    config_id: str = typer.Argument(..., help="BadWord ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a BadWord by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_badword(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            badword = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"BadWord Details: {badword.get('id', '-')}",
                badword,
                [
                    ("id", "id"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                    ("version_no", "version_no"),
                    ("crud_mode", "crud_mode"),
                    ("suggest_word", "suggest_word"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                ],
                transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve BadWord. {message} Status code: {status}", "BadWord", "get"))
            raise typer.Exit(code=status)


@badword_app.command("list")
def list_badwords(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List BadWords.
    """
    client = FessAPIClient(Settings())
    result = client.list_badwords(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            badwords = result.get("response", {}).get("settings", [])
            if not badwords:
                typer.echo("No BadWords found.")
            else:
                display_items = []
                for item in badwords:
                    d = dict(item)
                    d["updated_time_display"] = to_utc_iso8601(item.get("updated_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("BadWords", display_items, [
                    ("ID", "id"), ("SUGGEST_WORD", "suggest_word"), ("UPDATED_BY", "updated_by"),
                    ("UPDATED_TIME", "updated_time_display"), ("VERSION_NO", "version_no"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list BadWords. {message} Status code: {status}", "BadWord", "list"))
            raise typer.Exit(code=status)

# TODO upload
# TODO download
