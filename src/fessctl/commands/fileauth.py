import datetime
import json
from typing import Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import (
    format_detail_markdown,
    format_list_markdown,
    format_result_markdown,
    output_error,
    to_utc_iso8601,
)

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
            typer.echo(format_result_markdown(True, f"FileAuth '{fileauth_id}' created successfully.", "FileAuth", "create", fileauth_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create FileAuth. {message} Status code: {status}", "FileAuth", "create"))
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
        typer.echo(format_result_markdown(False, f"FileAuth with ID '{config_id}' not found. {message}", "FileAuth", "update"))
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
            typer.echo(format_result_markdown(True, f"FileAuth '{config_id}' updated successfully.", "FileAuth", "update", config_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update FileAuth. {message} Status code: {status}", "FileAuth", "update"))
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
            typer.echo(format_result_markdown(True, f"FileAuth '{config_id}' deleted successfully.", "FileAuth", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete FileAuth. {message} Status code: {status}", "FileAuth", "delete"))
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
    try:
        result = client.get_fileauth(config_id)
        status = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                fileauth = result.get("response", {}).get("setting", {})
                typer.echo(format_detail_markdown(
                    f"FileAuth Details: {fileauth.get('id', '-')}",
                    fileauth,
                    [
                        ("id", "id"),
                        ("updated_by", "updated_by"),
                        ("updated_time", "updated_time"),
                        ("version_no", "version_no"),
                        ("crud_mode", "crud_mode"),
                        ("hostname", "hostname"),
                        ("port", "port"),
                        ("protocol_scheme", "protocol_scheme"),
                        ("username", "username"),
                        ("password", "password"),
                        ("parameters", "parameters"),
                        ("file_config_id", "file_config_id"),
                        ("created_by", "created_by"),
                        ("created_time", "created_time"),
                    ],
                    transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
                ))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to retrieve FileAuth. {message} Status code: {status}", "FileAuth", "get"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "FileAuth", "get")
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
                typer.echo("No FileAuths found.")
            else:
                typer.echo(format_list_markdown("FileAuths", fileauths, [
                    ("ID", "id"), ("USERNAME", "username"),
                    ("HOSTNAME", "hostname"), ("PORT", "port"),
                    ("FILE_CONFIG ID", "file_config_id"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list FileAuths. {message} Status code: {status}", "FileAuth", "list"))
            raise typer.Exit(code=status)
