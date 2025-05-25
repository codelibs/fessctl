import datetime
import json
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import to_utc_iso8601

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
    client = FessAPIClient(Settings())(Settings())

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
            typer.secho(
                f"BadWord '{badword_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create BadWord. {message} Status code: {status}", fg=typer.colors.RED)
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
        typer.secho(
            f"BadWord with ID '{config_id}' not found. {message}",
            fg=typer.colors.RED,
        )
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
            typer.secho(
                f"BadWord '{config_id}' updated successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update BadWord. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
            typer.secho(
                f"BadWord '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete BadWord. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
            console = Console()
            table = Table(title=f"BadWord Details: {badword.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Correct output fields based on API schema
            table.add_row("id", str(badword.get("id", "-")))
            table.add_row("updated_by", str(badword.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                badword.get("updated_time")))
            table.add_row("version_no", str(badword.get("version_no", "-")))
            table.add_row("crud_mode", str(badword.get("crud_mode", "-")))
            table.add_row("suggest_word", str(
                badword.get("suggest_word", "-")))
            table.add_row("created_by", str(badword.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                badword.get("created_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve BadWord. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
                typer.secho("No BadWords found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="BadWords")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("SUGGEST_WORD", style="cyan")
                table.add_column("UPDATED_BY", style="cyan")
                table.add_column("UPDATED_TIME", style="cyan")
                table.add_column("VERSION_NO", style="cyan")

                for badword in badwords:
                    table.add_row(
                        badword.get("id", "-"),
                        badword.get("suggest_word", "-"),
                        badword.get("updated_by", "-"),
                        to_utc_iso8601(badword.get("updated_time")),
                        str(badword.get("version_no", "-")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list BadWords. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)

# TODO upload
# TODO download
