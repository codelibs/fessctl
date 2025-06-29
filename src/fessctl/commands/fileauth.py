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

fileauth_app = typer.Typer()


@fileauth_app.command("create")
def create_fileauth(
    username: str = typer.Option(..., "--username",
                                 help="Username for authentication"),
    file_config_id: str = typer.Option(...,
                                       "--file-config-id", help="FileConfig ID"),
    password: Optional[str] = typer.Option(
        None, "--password", help="Password"),
    hostname: Optional[str] = typer.Option(
        None, "--hostname", help="Target hostname"),
    port: Optional[int] = typer.Option(None, "--port", help="Target port"),
    protocol_scheme: Optional[str] = typer.Option(
        None, "--protocol-scheme", help="Protocol scheme (e.g., file, smb)"),
    parameters: Optional[str] = typer.Option(
        None, "--parameters", help="Additional parameters"),
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
    Create a new FileAuth.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "username": username,
        "file_config_id": file_config_id,
        "created_by": created_by,
        "created_time": created_time,
    }

    if password is not None:
        config["password"] = password
    if hostname is not None:
        config["hostname"] = hostname
    if port is not None:
        config["port"] = port
    if protocol_scheme is not None:
        config["protocol_scheme"] = protocol_scheme
    if parameters is not None:
        config["parameters"] = parameters

    result = client.create_fileauth(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            fileauth_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"FileAuth '{fileauth_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create FileAuth. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@fileauth_app.command("update")
def update_fileauth(
    config_id: str = typer.Argument(..., help="FileAuth ID"),
    username: Optional[str] = typer.Option(
        None, "--username", help="Username for authentication"),
    password: Optional[str] = typer.Option(
        None, "--password", help="Password"),
    hostname: Optional[str] = typer.Option(
        None, "--hostname", help="Target hostname"),
    port: Optional[int] = typer.Option(None, "--port", help="Target port"),
    protocol_scheme: Optional[str] = typer.Option(
        None, "--protocol-scheme", help="Protocol scheme (e.g., file, smb)"),
    parameters: Optional[str] = typer.Option(
        None, "--parameters", help="Additional parameters"),
    file_config_id: Optional[str] = typer.Option(
        None, "--file-config-id", help="Related FileConfig ID"),
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
    Update an existing FileAuth.
    """
    client = FessAPIClient(Settings())
    result = client.get_fileauth(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"FileAuth with ID '{config_id}' not found. {message}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if username is not None:
        config["username"] = username
    if password is not None:
        config["password"] = password
    if hostname is not None:
        config["hostname"] = hostname
    if port is not None:
        config["port"] = port
    if protocol_scheme is not None:
        config["protocol_scheme"] = protocol_scheme
    if parameters is not None:
        config["parameters"] = parameters
    if file_config_id is not None:
        config["file_config_id"] = file_config_id

    result = client.update_fileauth(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"FileAuth '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update FileAuth. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@fileauth_app.command("delete")
def delete_fileauth(
    config_id: str = typer.Argument(..., help="FileAuth ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a FileAuth by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_fileauth(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"FileAuth '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete FileAuth. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@fileauth_app.command("get")
def get_fileauth(
    config_id: str = typer.Argument(..., help="FileAuth ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a FileAuth by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_fileauth(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            fileauth = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(title=f"FileAuth Details: {fileauth.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Output fields (FileAuth public name fields only)
            table.add_row("id", str(fileauth.get("id", "-")))
            table.add_row("updated_by", str(fileauth.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                fileauth.get("updated_time")))
            table.add_row("version_no", str(fileauth.get("version_no", "-")))
            table.add_row("crud_mode", str(fileauth.get("crud_mode", "-")))
            table.add_row("hostname", str(fileauth.get("hostname", "-")))
            table.add_row("port", str(fileauth.get("port", "-")))
            table.add_row("protocol_scheme", str(
                fileauth.get("protocol_scheme", "-")))
            table.add_row("username", str(fileauth.get("username", "-")))
            table.add_row("password", str(fileauth.get("password", "-")))
            table.add_row("parameters", str(fileauth.get("parameters", "-")))
            table.add_row("file_config_id", str(
                fileauth.get("file_config_id", "-")))
            table.add_row("created_by", str(fileauth.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                fileauth.get("created_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve FileAuth. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)


@fileauth_app.command("list")
def list_fileauths(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List FileAuths.
    """
    client = FessAPIClient(Settings())
    result = client.list_fileauths(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            fileauths = result.get("response", {}).get("settings", [])
            if not fileauths:
                typer.secho("No FileAuths found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="FileAuths")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("USERNAME", style="cyan")
                table.add_column("HOSTNAME", style="cyan")
                table.add_column("PORT", style="cyan")
                table.add_column("FILE_CONFIG ID", style="cyan")

                for fileauth in fileauths:
                    table.add_row(
                        fileauth.get("id", "-"),
                        fileauth.get("username", "-"),
                        fileauth.get("hostname", "-"),
                        str(fileauth.get("port", "-")),
                        fileauth.get("file_config_id", "-"),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list FileAuths. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
