import datetime
import json
from typing import Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

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
    client = FessAPIClient(Settings())

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
            typer.echo(format_result_markdown(True, f"ReqHeader '{reqheader_id}' created successfully.", "ReqHeader", "create", reqheader_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create ReqHeader. {message} Status code: {status}", "ReqHeader", "create"))
            raise typer.Exit(code=status)


@reqheader_app.command("update")
def update_reqheader(
    reqheader_id: str = typer.Argument(..., help="ReqHeader ID"),
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
    client = FessAPIClient(Settings())
    result = client.get_reqheader(reqheader_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"ReqHeader '{reqheader_id}' not found. {message}", "ReqHeader", "update"))
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
            typer.echo(format_result_markdown(True, f"ReqHeader '{reqheader_id}' updated successfully.", "ReqHeader", "update", reqheader_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update ReqHeader. {message} Status code: {status}", "ReqHeader", "update"))
            raise typer.Exit(code=status)


@reqheader_app.command("delete")
def delete_reqheader(
    reqheader_id: str = typer.Argument(..., help="ReqHeader ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a ReqHeader by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_reqheader(reqheader_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"ReqHeader '{reqheader_id}' deleted successfully.", "ReqHeader", "delete", reqheader_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete ReqHeader. {message} Status code: {status}", "ReqHeader", "delete"))
            raise typer.Exit(code=status)


@reqheader_app.command("get")
def get_reqheader(
    reqheader_id: str = typer.Argument(..., help="ReqHeader ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a ReqHeader by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_reqheader(reqheader_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            reqheader = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"ReqHeader Details: {reqheader.get('id', '-')}",
                reqheader,
                [
                    ("id", "id"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                    ("version_no", "version_no"),
                    ("crud_mode", "crud_mode"),
                    ("hostname", "hostname"),
                    ("port", "port"),
                    ("auth_realm", "auth_realm"),
                    ("protocol_scheme", "protocol_scheme"),
                    ("username", "username"),
                    ("password", "password"),
                    ("parameters", "parameters"),
                    ("web_config_id", "web_config_id"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                ],
                transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve ReqHeader. {message} Status code: {status}", "ReqHeader", "get"))
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
    client = FessAPIClient(Settings())
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
                typer.echo("No ReqHeaders found.")
            else:
                typer.echo(format_list_markdown("ReqHeaders", reqheaders, [
                    ("ID", "id"),
                    ("NAME", "name"),
                    ("VALUE", "value"),
                    ("WEB_CONFIG_ID", "web_config_id"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list ReqHeaders. {message} Status code: {status}", "ReqHeader", "list"))
            raise typer.Exit(code=status)
