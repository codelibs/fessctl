import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.utils import to_utc_iso8601

reqheader_app = typer.Typer()


@reqheader_app.command("create")
def create_reqheader(
    name: str = typer.Option(..., "--name", help="Name of the request header"),
    value: str = typer.Option(..., "--value",
                              help="Value of the request header"),
    web_config_id: str = typer.Option(...,
                                      "--web-config-id", help="Web config ID"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Create a new ReqHeader.
    """
    client = FessAPIClient()

    config = {
        "crud_mode": 1,           # constant for create
        "name": name,             # required, max length 100
        "value": value,           # required, max length 1000
        "web_config_id": web_config_id,  # required, max length 1000
        "created_by": created_by,         # optional, max length 1000
        "created_time": created_time,     # UTC milliseconds
    }

    result = client.create_reqheader(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            reqheader_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"ReqHeader '{reqheader_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create ReqHeader. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@reqheader_app.command("update")
def update_reqheader(
    config_id: str = typer.Argument(..., help="ReqHeader ID"),
    name: Optional[str] = typer.Option(
        None, "--name", help="Name of the request header"),
    value: Optional[str] = typer.Option(
        None, "--value", help="Value of the request header"),
    web_config_id: Optional[str] = typer.Option(
        None, "--web-config-id", help="Web config ID"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Update an existing ReqHeader.
    """
    client = FessAPIClient()
    result = client.get_reqheader(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"ReqHeader '{config_id}' not found. {message}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if name is not None:
        config["name"] = name
    if value is not None:
        config["value"] = value
    if web_config_id is not None:
        config["web_config_id"] = web_config_id

    result = client.update_reqheader(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"ReqHeader '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update ReqHeader. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@reqheader_app.command("delete")
def delete_reqheader(
    config_id: str = typer.Argument(..., help="ReqHeader ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a ReqHeader by ID.
    """
    client = FessAPIClient()
    result = client.delete_reqheader(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"ReqHeader '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete ReqHeader. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@reqheader_app.command("get")
def get_reqheader(
    config_id: str = typer.Argument(..., help="ReqHeader ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a ReqHeader by ID.
    """
    client = FessAPIClient()
    result = client.get_reqheader(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            reqheader = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(
                title=f"ReqHeader Details: {reqheader.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Output fields (ReqHeader public name fields only)
            table.add_row("id", str(reqheader.get("id", "-")))
            table.add_row("updated_by", str(reqheader.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                reqheader.get("updated_time")))
            table.add_row("version_no", str(reqheader.get("version_no", "-")))
            table.add_row("crud_mode", str(reqheader.get("crud_mode", "-")))
            table.add_row("hostname", str(reqheader.get("hostname", "-")))
            table.add_row("port", str(reqheader.get("port", "-")))
            table.add_row("auth_realm", str(reqheader.get("auth_realm", "-")))
            table.add_row("protocol_scheme", str(
                reqheader.get("protocol_scheme", "-")))
            table.add_row("username", str(reqheader.get("username", "-")))
            table.add_row("password", str(reqheader.get("password", "-")))
            table.add_row("parameters", str(reqheader.get("parameters", "-")))
            table.add_row("web_config_id", str(
                reqheader.get("web_config_id", "-")))
            table.add_row("created_by", str(reqheader.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                reqheader.get("created_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve ReqHeader. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@reqheader_app.command("list")
def list_reqheaders(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    List ReqHeaders.
    """
    client = FessAPIClient()
    result = client.list_reqheaders(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            reqheaders = result.get("response", {}).get("settings", [])
            if not reqheaders:
                typer.secho("No ReqHeaders found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="ReqHeaders")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("NAME", style="cyan")
                table.add_column("VALUE", style="cyan")
                table.add_column("WEB_CONFIG_ID", style="cyan")

                for rh in reqheaders:
                    table.add_row(
                        rh.get("id", "-"),
                        rh.get("name", "-"),
                        rh.get("value", "-"),
                        rh.get("web_config_id", "-"),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list ReqHeaders. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
