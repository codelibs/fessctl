import datetime
import json
from typing import List, Optional

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

fileconfig_app = typer.Typer()


@fileconfig_app.command("create")
def create_fileconfig(
    name: str = typer.Option(..., "--name", help="FileConfig name"),
    paths: List[str] = typer.Option(..., "--path",
                                    help="Crawling target paths"),
    num_of_thread: int = typer.Option(
        1, "--num-of-thread", help="Number of crawling threads"
    ),
    interval_time: int = typer.Option(
        10000, "--interval-time", help="Crawling interval time (ms)"
    ),
    boost: float = typer.Option(1.0, "--boost", help="Boost value"),
    available: bool = typer.Option(
        True, "--available", help="Availability (true/false)"
    ),
    sort_order: int = typer.Option(1, "--sort-order", help="Sort order"),
    description: str = typer.Option("", "--description", help="Description"),
    label_type_ids: List[str] = typer.Option(
        [], "--label-type-id", help="Label type IDs"
    ),
    included_paths: List[str] = typer.Option(
        [], "--included-path", help="Included paths"
    ),
    excluded_paths: List[str] = typer.Option(
        [],
        "--excluded-path",
        help="Excluded paths",
    ),
    included_doc_paths: List[str] = typer.Option(
        [], "--included-doc-path", help="Included document paths"
    ),
    excluded_doc_paths: List[str] = typer.Option(
        [], "--excluded-doc-path", help="Excluded document paths"
    ),
    config_parameter: List[str] = typer.Option(
        [], "--config-parameter", help="Crawling config parameters"
    ),
    depth: int = typer.Option(1, "--depth", help="Crawling depth"),
    max_access_count: int = typer.Option(
        1000000, "--max-access-count", help="Maximum access count"
    ),
    permissions: List[str] = typer.Option(
        ["{role}guest"], "--permission", help="Access permissions"
    ),
    virtual_hosts: List[str] = typer.Option(
        [], "--virtual-host", help="Virtual hosts"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Create a new FileConfig.
    """
    client = FessAPIClient(Settings())
    config = {
        "crud_mode": 1,
        "name": name,
        "paths": "\n".join(paths),
        "num_of_thread": num_of_thread,
        "interval_time": interval_time,
        "boost": boost,
        "available": available,
        "sort_order": sort_order,
        "description": description,
        "label_type_ids": label_type_ids,
        "included_paths": "\n".join(included_paths),
        "excluded_paths": "\n".join(excluded_paths),
        "included_doc_paths": "\n".join(included_doc_paths),
        "excluded_doc_paths": "\n".join(excluded_doc_paths),
        "config_parameter": "\n".join(config_parameter),
        "depth": depth,
        "max_access_count": max_access_count,
        "permissions": "\n".join(permissions),
        "virtual_hosts": "\n".join(virtual_hosts),
        "created_by": created_by,
        "created_time": created_time,
    }

    result = client.create_fileconfig(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            config_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"FileConfig '{config_id}' created successfully.", "FileConfig", "create", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Operation failed. {message} Status code: {status}", "FileConfig", "create"))
            raise typer.Exit(code=status)


@fileconfig_app.command("update")
def update_fileconfig(
    config_id: str = typer.Argument(..., help="FileConfig ID"),
    name: Optional[str] = typer.Option(None, "--name", help="FileConfig name"),
    paths: Optional[List[str]] = typer.Option(
        None, "--path", help="Crawling target paths"
    ),
    num_of_thread: Optional[int] = typer.Option(
        None, "--num-of-thread", help="Number of crawling threads"
    ),
    interval_time: Optional[int] = typer.Option(
        None, "--interval-time", help="Crawling interval time (ms)"
    ),
    boost: Optional[float] = typer.Option(None, "--boost", help="Boost value"),
    available: Optional[bool] = typer.Option(
        None, "--available", help="Availability (true/false)"
    ),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Description"
    ),
    label_type_ids: Optional[List[str]] = typer.Option(
        None, "--label-type-id", help="Label type IDs"
    ),
    included_paths: Optional[List[str]] = typer.Option(
        None, "--included-path", help="Included paths"
    ),
    excluded_paths: Optional[List[str]] = typer.Option(
        None, "--excluded-path", help="Excluded paths"
    ),
    included_doc_paths: Optional[List[str]] = typer.Option(
        None, "--included-doc-path", help="Included document paths"
    ),
    excluded_doc_paths: Optional[List[str]] = typer.Option(
        None, "--excluded-doc-path", help="Excluded document paths"
    ),
    config_parameter: Optional[List[str]] = typer.Option(
        None, "--config-parameter", help="Crawling config parameters"
    ),
    depth: Optional[int] = typer.Option(
        None, "--depth", help="Crawling depth"),
    max_access_count: Optional[int] = typer.Option(
        None, "--max-access-count", help="Maximum access count"
    ),
    permissions: Optional[List[str]] = typer.Option(
        None, "--permission", help="Access permissions"
    ),
    virtual_hosts: Optional[List[str]] = typer.Option(
        None, "--virtual-host", help="Virtual hosts"
    ),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time (milliseconds UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Update an existing FileConfig.
    """
    client = FessAPIClient(Settings())
    result = client.get_fileconfig(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"FileConfig with ID '{config_id}' not found. {message}", "FileConfig", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if name is not None:
        config["name"] = name
    if paths is not None:
        config["paths"] = "\n".join(paths)
    if num_of_thread is not None:
        config["num_of_thread"] = num_of_thread
    if interval_time is not None:
        config["interval_time"] = interval_time
    if boost is not None:
        config["boost"] = boost
    if available is not None:
        config["available"] = available
    if sort_order is not None:
        config["sort_order"] = sort_order
    if description is not None:
        config["description"] = description
    if label_type_ids is not None:
        config["label_type_ids"] = label_type_ids
    if included_paths is not None:
        config["included_paths"] = "\n".join(included_paths)
    if excluded_paths is not None:
        config["excluded_paths"] = "\n".join(excluded_paths)
    if included_doc_paths is not None:
        config["included_doc_paths"] = "\n".join(included_doc_paths)
    if excluded_doc_paths is not None:
        config["excluded_doc_paths"] = "\n".join(excluded_doc_paths)
    if config_parameter is not None:
        config["config_parameter"] = "\n".join(config_parameter)
    if depth is not None:
        config["depth"] = depth
    if max_access_count is not None:
        config["max_access_count"] = max_access_count
    if permissions is not None:
        config["permissions"] = "\n".join(permissions)
    if virtual_hosts is not None:
        config["virtual_hosts"] = "\n".join(virtual_hosts)

    result = client.update_fileconfig(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            config_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"FileConfig '{config_id}' updated successfully.", "FileConfig", "update", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Operation failed. {message} Status code: {status}", "FileConfig", "update"))
            raise typer.Exit(code=status)


@fileconfig_app.command("delete")
def delete_fileconfig(
    config_id: str = typer.Argument(..., help="FileConfig ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a FileConfig by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_fileconfig(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"FileConfig '{config_id}' deleted successfully.", "FileConfig", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete FileConfig. {message} Status code: {status}", "FileConfig", "delete"))
            raise typer.Exit(code=status)


@fileconfig_app.command("get")
def get_fileconfig(
    config_id: str = typer.Argument(..., help="FileConfig ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Retrieve a FileConfig by ID.
    """
    client = FessAPIClient(Settings())
    try:
        result = client.get_fileconfig(config_id)
        status = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                fileconfig = result.get("response", {}).get("setting", {})
                typer.echo(format_detail_markdown(
                    f"FileConfig Details: {fileconfig.get('name', '-')}",
                    fileconfig,
                    [
                        ("id", "id"),
                        ("updated_by", "updated_by"),
                        ("updated_time", "updated_time"),
                        ("version_no", "version_no"),
                        ("label_type_ids", "label_type_ids"),
                        ("crud_mode", "crud_mode"),
                        ("name", "name"),
                        ("description", "description"),
                        ("paths", "paths"),
                        ("included_paths", "included_paths"),
                        ("excluded_paths", "excluded_paths"),
                        ("included_doc_paths", "included_doc_paths"),
                        ("excluded_doc_paths", "excluded_doc_paths"),
                        ("config_parameter", "config_parameter"),
                        ("depth", "depth"),
                        ("max_access_count", "max_access_count"),
                        ("num_of_thread", "num_of_thread"),
                        ("interval_time", "interval_time"),
                        ("boost", "boost"),
                        ("available", "available"),
                        ("permissions", "permissions"),
                        ("virtual_hosts", "virtual_hosts"),
                        ("sort_order", "sort_order"),
                        ("created_by", "created_by"),
                        ("created_time", "created_time"),
                    ],
                    transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
                ))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to retrieve FileConfig. {message} Status code: {status}", "FileConfig", "get"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "FileConfig", "get")
        raise typer.Exit(code=1)


@fileconfig_app.command("list")
def list_fileconfigs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List FileConfigs.
    """
    client = FessAPIClient(Settings())
    result = client.list_fileconfigs(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            configs = result.get("response", {}).get("settings", [])
            if not configs:
                typer.echo("No FileConfigs found.")
            else:
                typer.echo(format_list_markdown("FileConfigs", configs, [
                    ("ID", "id"), ("Name", "name"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list FileConfigs. {message} Status code: {status}", "FileConfig", "list"))
            raise typer.Exit(code=status)
