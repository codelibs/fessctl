import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.utils import to_utc_iso8601

accesstoken_app = typer.Typer()


@accesstoken_app.command("create")
def create_accesstoken(
    name: str = typer.Option(..., "--name", help="AccessToken name"),
    token: Optional[str] = typer.Option(None, "--token", help="Access token string"),
    permissions: Optional[List[str]] = typer.Option(
        [], "--permission", help="Access permissions"
    ),
    parameter_name: Optional[str] = typer.Option(
        None, "--parameter-name", help="Parameter name to send the token"
    ),
    expires: Optional[str] = typer.Option(
        None, "--expires", help="Expiration time (format: yyyy-MM-ddTHH:mm:ss)"
    ),
    created_by: Optional[str] = typer.Option(
        "admin", "--created-by", help="Created by"
    ),
    created_time: Optional[int] = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Create a new AccessToken.
    """
    client = FessAPIClient()

    config = {
        "crud_mode": 1,
        "name": name,
        "token": token,
        "permissions": "\n".join(permissions),
        "parameter_name": parameter_name,
        "expires": expires,
        "created_by": created_by,
        "created_time": created_time,
    }

    result = client.create_accesstoken(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            accesstoken_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"AccessToken '{accesstoken_id}' created successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Operation failed. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@accesstoken_app.command("update")
def update_accesstoken(
    accesstoken_id: str = typer.Argument(..., help="AccessToken ID"),
    name: Optional[str] = typer.Option(None, "--name", help="AccessToken name"),
    token: Optional[str] = typer.Option(None, "--token", help="Access token string"),
    permissions: Optional[List[str]] = typer.Option(
        None, "--permission", help="Access permissions"
    ),
    parameter_name: Optional[str] = typer.Option(
        None, "--parameter-name", help="Parameter name"
    ),
    expires: Optional[str] = typer.Option(
        None, "--expires", help="Expiration datetime (format: YYYY-MM-DDTHH:MM:SS)"
    ),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Update an existing AccessToken.
    """
    client = FessAPIClient()
    result = client.get_accesstoken(accesstoken_id)

    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"AccessToken with ID '{accesstoken_id}' not found. {message}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if name is not None:
        config["name"] = name
    if token is not None:
        config["token"] = token
    if permissions is not None:
        config["permissions"] = "\n".join(permissions)
    if parameter_name is not None:
        config["parameter_name"] = parameter_name
    if expires is not None:
        config["expires"] = expires

    result = client.update_accesstoken(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            accesstoken_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"AccessToken '{accesstoken_id}' updated successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update AccessToken. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@accesstoken_app.command("delete")
def delete_accesstoken(
    accesstoken_id: str = typer.Argument(..., help="AccessToken ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete a AccessToken by ID.
    """
    client = FessAPIClient()
    result = client.delete_accesstoken(accesstoken_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"AccessToken '{accesstoken_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete AccessToken. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@accesstoken_app.command("get")
def get_accesstoken(
    accesstoken_id: str = typer.Argument(..., help="AccessToken ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Retrieve an AccessToken by ID.
    """
    client = FessAPIClient()
    result = client.get_accesstoken(accesstoken_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            accesstoken = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(title=f"AccessToken Details: {accesstoken.get('name', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Output each field according to the latest AccessToken schema
            table.add_row("id", str(accesstoken.get("id", "-")))
            table.add_row("updated_by", str(accesstoken.get("updated_by", "-")))
            table.add_row(
                "updated_time", to_utc_iso8601(accesstoken.get("updated_time"))
            )
            table.add_row("version_no", str(accesstoken.get("version_no", "-")))
            table.add_row("name", str(accesstoken.get("name", "-")))
            table.add_row("token", str(accesstoken.get("token", "-")))
            table.add_row("permissions", str(accesstoken.get("permissions", "-")))
            table.add_row("parameter_name", str(accesstoken.get("parameter_name", "-")))
            table.add_row("expires", str(accesstoken.get("expires", "-")))
            table.add_row("created_by", str(accesstoken.get("created_by", "-")))
            table.add_row(
                "created_time", to_utc_iso8601(accesstoken.get("created_time"))
            )

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve AccessToken. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@accesstoken_app.command("list")
def list_accesstokens(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List AccessTokens.
    """
    client = FessAPIClient()
    result = client.list_accesstokens(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            accesstokens = result.get("response", {}).get("settings", [])
            if not accesstokens:
                typer.secho("No AccessTokens found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="AccessTokens")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("NAME", style="cyan", no_wrap=True)
                table.add_column("EXPIRES", style="cyan", no_wrap=True)
                table.add_column("PERMISSIONS", style="cyan", no_wrap=False)
                for accesstoken in accesstokens:
                    table.add_row(
                        accesstoken.get("id", "-"),
                        accesstoken.get("name", "-"),
                        accesstoken.get("expires", "-"),
                        accesstoken.get("permissions", "-"),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list AccessTokens. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
