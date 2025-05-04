import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.utils import to_utc_iso8601

keymatch_app = typer.Typer()


@keymatch_app.command("create")
def create_keymatch(
    term: str = typer.Option(..., "--term", help="Search term to match"),
    query: str = typer.Option(..., "--query",
                              help="Query to execute when term matches"),
    max_size: int = typer.Option(..., "--max-size",
                                 help="Maximum result size"),
    boost: float = typer.Option(..., "--boost", help="Boost value"),
    version_no: int = typer.Option(..., "--version-no", help="Version number"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host condition"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new KeyMatch.
    """
    client = FessAPIClient()

    config = {
        "crud_mode": 1,
        "term": term,
        "query": query,
        "max_size": max_size,
        "boost": boost,
        "version_no": version_no,
        "created_by": created_by,
        "created_time": created_time,
    }
    if virtual_host:
        config["virtual_host"] = virtual_host

    result = client.create_keymatch(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            keymatch_id = result.get("response", {}).get("id", "-")
            typer.secho(
                f"KeyMatch '{keymatch_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create KeyMatch. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@keymatch_app.command("update")
def update_keymatch(
    config_id: str = typer.Argument(..., help="KeyMatch ID"),
    term: Optional[str] = typer.Option(
        None, "--term", help="Search term to match"),
    query: Optional[str] = typer.Option(
        None, "--query", help="Query to execute when term matches"),
    max_size: Optional[int] = typer.Option(
        None, "--max-size", help="Maximum result size"),
    boost: Optional[float] = typer.Option(None, "--boost", help="Boost value"),
    version_no: Optional[int] = typer.Option(
        None, "--version-no", help="Version number"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host condition"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Update an existing KeyMatch.
    """
    client = FessAPIClient()
    result = client.get_keymatch(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"KeyMatch with ID '{config_id}' not found. {message}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if term is not None:
        config["term"] = term
    if query is not None:
        config["query"] = query
    if max_size is not None:
        config["max_size"] = max_size
    if boost is not None:
        config["boost"] = boost
    if version_no is not None:
        config["version_no"] = version_no
    if virtual_host is not None:
        config["virtual_host"] = virtual_host

    result = client.update_keymatch(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"KeyMatch '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update KeyMatch. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@keymatch_app.command("delete")
def delete_keymatch(
    config_id: str = typer.Argument(..., help="KeyMatch ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a KeyMatch by ID.
    """
    client = FessAPIClient()
    result = client.delete_keymatch(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"KeyMatch '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete KeyMatch. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@keymatch_app.command("get")
def get_keymatch(
    config_id: str = typer.Argument(..., help="KeyMatch ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a KeyMatch by ID.
    """
    client = FessAPIClient()
    result = client.get_keymatch(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            keymatch = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(title=f"KeyMatch Details: {keymatch.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row("id", str(keymatch.get("id", "-")))
            table.add_row("term", str(keymatch.get("term", "-")))
            table.add_row("query", str(keymatch.get("query", "-")))
            table.add_row("max_size", str(keymatch.get("max_size", "-")))
            table.add_row("boost", str(keymatch.get("boost", "-")))
            table.add_row("virtual_host", str(
                keymatch.get("virtual_host", "-")))
            table.add_row("version_no", str(keymatch.get("version_no", "-")))
            table.add_row("crud_mode", str(keymatch.get("crud_mode", "-")))
            table.add_row("created_by", str(keymatch.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                keymatch.get("created_time")))
            table.add_row("updated_by", str(keymatch.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                keymatch.get("updated_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve KeyMatch. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@keymatch_app.command("list")
def list_keymatchs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List KeyMatchs.
    """
    client = FessAPIClient()
    result = client.list_keymatchs(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            keymatchs = result.get("response", {}).get("settings", [])
            if not keymatchs:
                typer.secho("No KeyMatchs found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="KeyMatchs")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("TERM", style="green")
                table.add_column("QUERY", style="magenta")
                table.add_column("BOOST", style="yellow")
                table.add_column("MAX SIZE", style="blue")
                table.add_column("UPDATED BY", style="white")
                table.add_column("UPDATED TIME", style="white")

                for km in keymatchs:
                    table.add_row(
                        km.get("id", "-"),
                        km.get("term", "-"),
                        km.get("query", "-"),
                        str(km.get("boost", "-")),
                        str(km.get("max_size", "-")),
                        km.get("updated_by", "-"),
                        to_utc_iso8601(km.get("updated_time")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list KeyMatchs. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
