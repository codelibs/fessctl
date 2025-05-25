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

webauth_app = typer.Typer()


@webauth_app.command("create")
def create_webauth(
    username: str = typer.Option(..., "--username",
                                 help="Username for authentication"),
    web_config_id: str = typer.Option(...,
                                      "--web-config-id", help="WebConfig ID"),
    password: Optional[str] = typer.Option(
        None, "--password", help="Password"),
    hostname: Optional[str] = typer.Option(
        None, "--hostname", help="Target hostname"),
    port: Optional[int] = typer.Option(None, "--port", help="Target port"),
    auth_realm: Optional[str] = typer.Option(
        None, "--auth-realm", help="Authentication realm"),
    protocol_scheme: Optional[str] = typer.Option(
        None, "--protocol-scheme", help="Protocol scheme (e.g., http, https)"),
    parameters: Optional[str] = typer.Option(
        None, "--parameters", help="Additional parameters"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new WebAuth.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "username": username,
        "web_config_id": web_config_id,
        "created_by": created_by,
        "created_time": created_time,
    }

    # Optional fields
    if password is not None:
        config["password"] = password
    if hostname is not None:
        config["hostname"] = hostname
    if port is not None:
        config["port"] = port
    if auth_realm is not None:
        config["auth_realm"] = auth_realm
    if protocol_scheme is not None:
        config["protocol_scheme"] = protocol_scheme
    if parameters is not None:
        config["parameters"] = parameters

    result = client.create_webauth(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            webauth_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"WebAuth '{webauth_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create WebAuth. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@webauth_app.command("update")
def update_webauth(
    config_id: str = typer.Argument(..., help="WebAuth ID"),
    username: Optional[str] = typer.Option(
        None, "--username", help="Username for authentication"),
    password: Optional[str] = typer.Option(
        None, "--password", help="Password"),
    hostname: Optional[str] = typer.Option(
        None, "--hostname", help="Target hostname"),
    port: Optional[int] = typer.Option(None, "--port", help="Target port"),
    auth_realm: Optional[str] = typer.Option(
        None, "--auth-realm", help="Authentication realm"),
    protocol_scheme: Optional[str] = typer.Option(
        None, "--protocol-scheme", help="Protocol scheme (e.g., http, https)"),
    parameters: Optional[str] = typer.Option(
        None, "--parameters", help="Additional parameters"),
    web_config_id: Optional[str] = typer.Option(
        None, "--web-config-id", help="Related WebConfig ID"),
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
    Update an existing WebAuth.
    """
    client = FessAPIClient(Settings())
    result = client.get_webauth(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"WebAuth with ID '{config_id}' not found. {message}",
            fg=typer.colors.RED,
        )
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
    if auth_realm is not None:
        config["auth_realm"] = auth_realm
    if protocol_scheme is not None:
        config["protocol_scheme"] = protocol_scheme
    if parameters is not None:
        config["parameters"] = parameters
    if web_config_id is not None:
        config["web_config_id"] = web_config_id

    result = client.update_webauth(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"WebAuth '{config_id}' updated successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update WebAuth. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@webauth_app.command("delete")
def delete_webauth(
    config_id: str = typer.Argument(..., help="WebAuth ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a WebAuth by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_webauth(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"WebAuth '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete WebAuth. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@webauth_app.command("get")
def get_webauth(
    config_id: str = typer.Argument(..., help="WebAuth ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a WebAuth by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_webauth(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            webauth = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(title=f"WebAuth Details: {webauth.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Output fields (WebAuth public name fields only)
            table.add_row("id", str(webauth.get("id", "-")))
            table.add_row("updated_by", str(webauth.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                webauth.get("updated_time")))
            table.add_row("version_no", str(webauth.get("version_no", "-")))
            table.add_row("crud_mode", str(webauth.get("crud_mode", "-")))
            table.add_row("hostname", str(webauth.get("hostname", "-")))
            table.add_row("port", str(webauth.get("port", "-")))
            table.add_row("auth_realm", str(webauth.get("auth_realm", "-")))
            table.add_row("protocol_scheme", str(
                webauth.get("protocol_scheme", "-")))
            table.add_row("username", str(webauth.get("username", "-")))
            table.add_row("password", str(webauth.get("password", "-")))
            table.add_row("parameters", str(webauth.get("parameters", "-")))
            table.add_row("web_config_id", str(
                webauth.get("web_config_id", "-")))
            table.add_row("created_by", str(webauth.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                webauth.get("created_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve WebAuth. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@webauth_app.command("list")
def list_webauths(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List WebAuths.
    """
    client = FessAPIClient(Settings())
    result = client.list_webauths(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            webauths = result.get("response", {}).get("settings", [])
            if not webauths:
                typer.secho("No WebAuths found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="WebAuths")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("USERNAME", style="cyan")
                table.add_column("HOSTNAME", style="cyan")
                table.add_column("PORT", style="cyan")
                table.add_column("WEB_CONFIG ID", style="cyan")

                for webauth in webauths:
                    table.add_row(
                        webauth.get("id", "-"),
                        webauth.get("username", "-"),
                        webauth.get("hostname", "-"),
                        str(webauth.get("port", "-")),
                        webauth.get("web_config_id", "-"),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list WebAuths. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
