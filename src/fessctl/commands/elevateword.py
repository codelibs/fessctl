import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.utils import to_utc_iso8601

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
    client = FessAPIClient()

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
            typer.secho(
                f"ElevateWord '{eid}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create ElevateWord. {message} Status code: {status}", fg=typer.colors.RED)
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
    client = FessAPIClient()
    result = client.get_elevateword(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"ElevateWord with ID '{config_id}' not found. {message}", fg=typer.colors.RED)
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
            typer.secho(
                f"ElevateWord '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update ElevateWord. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@elevateword_app.command("delete")
def delete_elevateword(
    config_id: str = typer.Argument(..., help="ElevateWord ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a ElevateWord by ID.
    """
    client = FessAPIClient()
    result = client.delete_elevateword(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"ElevateWord '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete ElevateWord. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
    client = FessAPIClient()
    result = client.get_elevateword(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            elevateword = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(
                title=f"ElevateWord Details: {elevateword.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # 正しい public name に基づいたフィールドのみ表示
            table.add_row("id", str(elevateword.get("id", "-")))
            table.add_row("suggest_word", str(
                elevateword.get("suggest_word", "-")))
            table.add_row("boost", str(elevateword.get("boost", "-")))
            table.add_row("version_no", str(
                elevateword.get("version_no", "-")))
            table.add_row("label_type_ids", ", ".join(
                elevateword.get("label_type_ids", [])))
            table.add_row("reading", str(elevateword.get("reading", "-")))
            table.add_row("target_label", str(
                elevateword.get("target_label", "-")))
            table.add_row("permissions", str(
                elevateword.get("permissions", "-")))
            table.add_row("crud_mode", str(elevateword.get("crud_mode", "-")))
            table.add_row("created_by", str(
                elevateword.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                elevateword.get("created_time")))
            table.add_row("updated_by", str(
                elevateword.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                elevateword.get("updated_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve ElevateWord. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


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
    client = FessAPIClient()
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
                typer.secho("No ElevateWords found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="ElevateWords")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("SUGGEST WORD", style="green")
                table.add_column("BOOST", style="magenta")
                table.add_column("VERSION NO", style="yellow")
                table.add_column("UPDATED BY", style="blue")
                table.add_column("UPDATED TIME", style="white")

                for ew in elevatewords:
                    table.add_row(
                        ew.get("id", "-"),
                        ew.get("suggest_word", "-"),
                        str(ew.get("boost", "-")),
                        str(ew.get("version_no", "-")),
                        ew.get("updated_by", "-"),
                        to_utc_iso8601(ew.get("updated_time")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list ElevateWords. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
