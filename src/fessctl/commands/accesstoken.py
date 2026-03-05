import datetime
import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

accesstoken_app = typer.Typer()


@accesstoken_app.command("create")
def create_accesstoken(
    name: str = typer.Option(..., "--name", help="AccessToken name"),
    token: Optional[str] = typer.Option(
        None, "--token", help="Access token string"),
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
    client = FessAPIClient(Settings())

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
            typer.echo(format_result_markdown(True, f"AccessToken '{accesstoken_id}' created successfully.", "AccessToken", "create", accesstoken_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Operation failed. {message} Status code: {status}", "AccessToken", "create"))
            raise typer.Exit(code=status)


@accesstoken_app.command("update")
def update_accesstoken(
    accesstoken_id: str = typer.Argument(..., help="AccessToken ID"),
    name: Optional[str] = typer.Option(
        None, "--name", help="AccessToken name"),
    token: Optional[str] = typer.Option(
        None, "--token", help="Access token string"),
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
    client = FessAPIClient(Settings())
    result = client.get_accesstoken(accesstoken_id)

    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"AccessToken with ID '{accesstoken_id}' not found. {message}", "AccessToken", "update"))
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
            typer.echo(format_result_markdown(True, f"AccessToken '{accesstoken_id}' updated successfully.", "AccessToken", "update", accesstoken_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update AccessToken. {message} Status code: {status}", "AccessToken", "update"))
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
    client = FessAPIClient(Settings())
    result = client.delete_accesstoken(accesstoken_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"AccessToken '{accesstoken_id}' deleted successfully.", "AccessToken", "delete", accesstoken_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete AccessToken. {message} Status code: {status}", "AccessToken", "delete"))
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
    client = FessAPIClient(Settings())
    result = client.get_accesstoken(accesstoken_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            accesstoken = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"AccessToken Details: {accesstoken.get('name', '-')}",
                accesstoken,
                [
                    ("id", "id"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                    ("version_no", "version_no"),
                    ("name", "name"),
                    ("token", "token"),
                    ("permissions", "permissions"),
                    ("parameter_name", "parameter_name"),
                    ("expires", "expires"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                ],
                transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve AccessToken. {message} Status code: {status}", "AccessToken", "get"))
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
    client = FessAPIClient(Settings())
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
                typer.echo("No AccessTokens found.")
            else:
                typer.echo(format_list_markdown("AccessTokens", accesstokens, [
                    ("ID", "id"), ("NAME", "name"), ("EXPIRES", "expires"), ("PERMISSIONS", "permissions"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list AccessTokens. {message} Status code: {status}", "AccessToken", "list"))
            raise typer.Exit(code=status)
