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
    to_utc_iso8601,
)

duplicatehost_app = typer.Typer()


@duplicatehost_app.command("create")
def create_duplicatehost(
    regular_name: str = typer.Option(...,
                                     "--regular-name", help="Regular host name"),
    duplicate_host_name: str = typer.Option(
        ..., "--duplicate-host-name", help="Duplicate host name"
    ),
    sort_order: int = typer.Option(
        ..., "--sort-order", help="Sort order (non-negative integer)"
    ),
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
    Create a new DuplicateHost.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "regular_name": regular_name,
        "duplicate_host_name": duplicate_host_name,
        "sort_order": sort_order,
        "created_by": created_by,
        "created_time": created_time,
    }

    result = client.create_duplicatehost(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            dup_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"DuplicateHost '{dup_id}' created successfully.", "DuplicateHost", "create", dup_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create DuplicateHost. {message} Status code: {status}", "DuplicateHost", "create"))
            raise typer.Exit(code=status)


@duplicatehost_app.command("update")
def update_duplicatehost(
    config_id: str = typer.Argument(..., help="DuplicateHost ID"),
    regular_name: Optional[str] = typer.Option(
        None, "--regular-name", help="Regular host name"
    ),
    duplicate_host_name: Optional[str] = typer.Option(
        None, "--duplicate-host-name", help="Duplicate host name"
    ),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order (non-negative integer)"
    ),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Update an existing DuplicateHost.
    """
    client = FessAPIClient(Settings())
    result = client.get_duplicatehost(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"DuplicateHost with ID '{config_id}' not found. {message}", "DuplicateHost", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if regular_name is not None:
        config["regular_name"] = regular_name
    if duplicate_host_name is not None:
        config["duplicate_host_name"] = duplicate_host_name
    if sort_order is not None:
        config["sort_order"] = sort_order

    result = client.update_duplicatehost(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"DuplicateHost '{config_id}' updated successfully.", "DuplicateHost", "update", config_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update DuplicateHost. {message} Status code: {status}", "DuplicateHost", "update"))
            raise typer.Exit(code=status)


@duplicatehost_app.command("delete")
def delete_duplicatehost(
    config_id: str = typer.Argument(..., help="DuplicateHost ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete a DuplicateHost by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_duplicatehost(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"DuplicateHost '{config_id}' deleted successfully.", "DuplicateHost", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete DuplicateHost. {message} Status code: {status}", "DuplicateHost", "delete"))
            raise typer.Exit(code=status)


@duplicatehost_app.command("get")
def get_duplicatehost(
    config_id: str = typer.Argument(..., help="DuplicateHost ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Retrieve a DuplicateHost by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_duplicatehost(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            duplicatehost = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"DuplicateHost Details: {duplicatehost.get('id', '-')}",
                duplicatehost,
                [
                    ("id", "id"),
                    ("regular_name", "regular_name"),
                    ("duplicate_host_name", "duplicate_host_name"),
                    ("sort_order", "sort_order"),
                    ("version_no", "version_no"),
                    ("crud_mode", "crud_mode"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                ],
                transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve DuplicateHost. {message} Status code: {status}", "DuplicateHost", "get"))
            raise typer.Exit(code=status)


@duplicatehost_app.command("list")
def list_duplicatehosts(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List DuplicateHosts.
    """
    client = FessAPIClient(Settings())
    result = client.list_duplicatehosts(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            duplicatehosts = result.get("response", {}).get("settings", [])
            if not duplicatehosts:
                typer.echo("No DuplicateHosts found.")
            else:
                display_items = []
                for dh in duplicatehosts:
                    d = dict(dh)
                    d["updated_time_display"] = to_utc_iso8601(dh.get("updated_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("DuplicateHosts", display_items, [
                    ("ID", "id"), ("REGULAR NAME", "regular_name"),
                    ("DUPLICATE HOST NAME", "duplicate_host_name"),
                    ("SORT ORDER", "sort_order"), ("UPDATED BY", "updated_by"),
                    ("UPDATED TIME", "updated_time_display"),
                ]))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list DuplicateHosts. {message} Status code: {status}", "DuplicateHost", "list"))
            raise typer.Exit(code=status)
