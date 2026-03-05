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

    result = client.create_pathmap(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            path_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"Path Mapping '{path_id}' created successfully.", "PathMap", "create", path_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create Path Mapping. {message} Status code: {status}", "PathMap", "create"))
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
        typer.echo(format_result_markdown(False, f"PathMap with ID '{config_id}' not found. {message}", "PathMap", "update"))
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
            typer.echo(format_result_markdown(True, f"PathMap '{config_id}' updated successfully.", "PathMap", "update", config_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update PathMap. {message} Status code: {status}", "PathMap", "update"))
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
            typer.echo(format_result_markdown(True, f"PathMap '{config_id}' deleted successfully.", "PathMap", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete PathMap. {message} Status code: {status}", "PathMap", "delete"))
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
            typer.echo(format_detail_markdown(
                f"PathMap Details: {pathmap.get('id', '-')}",
                pathmap,
                [
                    ("id", "id"),
                    ("regex", "regex"),
                    ("replacement", "replacement"),
                    ("process_type", "process_type"),
                    ("sort_order", "sort_order"),
                    ("user_agent", "user_agent"),
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
            typer.echo(format_result_markdown(False, f"Failed to retrieve PathMap. {message} Status code: {status}", "PathMap", "get"))
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
                typer.echo("No PathMaps found.")
            else:
                typer.echo(format_list_markdown("PathMaps", pathmaps, [
                    ("ID", "id"), ("REGEX", "regex"),
                    ("REPLACEMENT", "replacement"), ("PROCESS TYPE", "process_type"),
                    ("SORT ORDER", "sort_order"), ("USER AGENT", "user_agent"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list PathMaps. {message} Status code: {status}", "PathMap", "list"))
            raise typer.Exit(code=status)
