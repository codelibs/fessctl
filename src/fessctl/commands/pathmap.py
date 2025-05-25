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

pathmap_app = typer.Typer()


@pathmap_app.command("create")
def create_path(
    regex: str = typer.Option(..., "--regex", help="Regex pattern to match"),
    process_type: str = typer.Option(...,
                                     "--process-type", help="Process type"),
    replacement: Optional[str] = typer.Option(
        None, "--replacement", help="Replacement string"),
    sort_order: int = typer.Option(0, "--sort-order", help="Sort order"),
    user_agent: Optional[str] = typer.Option(
        None, "--user-agent", help="User agent"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Create a new Path Mapping.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "regex": regex,
        "process_type": process_type,
        "sort_order": sort_order,
        "created_by": created_by,
        "created_time": created_time,
    }

    if replacement is not None:
        config["replacement"] = replacement
    if user_agent is not None:
        config["user_agent"] = user_agent

    result = client.create_path(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            path_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"Path Mapping '{path_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create Path Mapping. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@pathmap_app.command("update")
def update_pathmap(
    config_id: str = typer.Argument(..., help="PathMap ID"),
    regex: Optional[str] = typer.Option(
        None, "--regex", help="Regex pattern to match"),
    process_type: Optional[str] = typer.Option(
        None, "--process-type", help="Process type"),
    replacement: Optional[str] = typer.Option(
        None, "--replacement", help="Replacement string"),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    user_agent: Optional[str] = typer.Option(
        None, "--user-agent", help="User agent"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Update an existing PathMap.
    """
    client = FessAPIClient(Settings())
    result = client.get_pathmap(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"PathMap with ID '{config_id}' not found. {message}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if regex is not None:
        config["regex"] = regex
    if process_type is not None:
        config["process_type"] = process_type
    if replacement is not None:
        config["replacement"] = replacement
    if sort_order is not None:
        config["sort_order"] = sort_order
    if user_agent is not None:
        config["user_agent"] = user_agent

    result = client.update_pathmap(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"PathMap '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update PathMap. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@pathmap_app.command("delete")
def delete_pathmap(
    config_id: str = typer.Argument(..., help="PathMap ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a PathMap by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_pathmap(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"PathMap '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete PathMap. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@pathmap_app.command("get")
def get_pathmap(
    config_id: str = typer.Argument(..., help="PathMap ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a PathMap by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_pathmap(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            pathmap = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(title=f"PathMap Details: {pathmap.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # 正しい PathMap パラメータ出力
            table.add_row("id", str(pathmap.get("id", "-")))
            table.add_row("regex", str(pathmap.get("regex", "-")))
            table.add_row("replacement", str(pathmap.get("replacement", "-")))
            table.add_row("process_type", str(
                pathmap.get("process_type", "-")))
            table.add_row("sort_order", str(pathmap.get("sort_order", "-")))
            table.add_row("user_agent", str(pathmap.get("user_agent", "-")))
            table.add_row("version_no", str(pathmap.get("version_no", "-")))
            table.add_row("crud_mode", str(pathmap.get("crud_mode", "-")))
            table.add_row("updated_by", str(pathmap.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                pathmap.get("updated_time")))
            table.add_row("created_by", str(pathmap.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                pathmap.get("created_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve PathMap. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@pathmap_app.command("list")
def list_pathmaps(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List PathMaps.
    """
    client = FessAPIClient(Settings())
    result = client.list_pathmaps(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            pathmaps = result.get("response", {}).get("settings", [])
            if not pathmaps:
                typer.secho("No PathMaps found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="PathMaps")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("REGEX", style="magenta")
                table.add_column("REPLACEMENT", style="green")
                table.add_column("PROCESS TYPE", style="blue")
                table.add_column("SORT ORDER", justify="right")
                table.add_column("USER AGENT", style="yellow")

                for pathmap in pathmaps:
                    table.add_row(
                        pathmap.get("id", "-"),
                        pathmap.get("regex", "-"),
                        pathmap.get("replacement", "-"),
                        pathmap.get("process_type", "-"),
                        str(pathmap.get("sort_order", "-")),
                        pathmap.get("user_agent", "-"),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list PathMaps. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
