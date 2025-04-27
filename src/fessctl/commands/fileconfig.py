import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient

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
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Create a new FileConfig.
    """
    client = FessAPIClient()
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

    _handle_response(
        client.create_fileconfig(config),
        output,
        success_message="FileConfig created successfully.",
    )


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
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Update an existing FileConfig.
    """
    client = FessAPIClient()
    result = client.get_fileconfig(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"FileConfig with ID '{config_id}' not found. {message}",
            fg=typer.colors.RED,
        )
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

    _handle_response(
        client.update_fileconfig(config),
        output,
        success_message="FileConfig updated successfully.",
    )


@fileconfig_app.command("delete")
def delete_fileconfig(
    config_id: str = typer.Argument(..., help="FileConfig ID"),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Delete a FileConfig by ID.
    """
    client = FessAPIClient()
    _handle_response(
        client.delete_fileconfig(config_id),
        output,
        success_message=f"FileConfig '{config_id}' deleted successfully.",
    )


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
    client = FessAPIClient()
    result = client.get_fileconfig(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            fileconfig = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(
                title=f"FileConfig Details: {fileconfig.get('name', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Output all public fields
            table.add_row("id", str(fileconfig.get("id", "-")))
            table.add_row("updated_by", str(fileconfig.get("updated_by", "-")))
            table.add_row("updated_time", str(
                fileconfig.get("updated_time", "-")))
            table.add_row("version_no", str(fileconfig.get("version_no", "-")))
            table.add_row(
                "label_type_ids", ", ".join(
                    fileconfig.get("label_type_ids", []))
            )
            table.add_row("crud_mode", str(fileconfig.get("crud_mode", "-")))
            table.add_row("name", str(fileconfig.get("name", "-")))
            table.add_row("description", str(
                fileconfig.get("description", "-")))
            table.add_row("paths", str(fileconfig.get("paths", "-")))
            table.add_row("included_paths", str(
                fileconfig.get("included_paths", "-")))
            table.add_row("excluded_paths", str(
                fileconfig.get("excluded_paths", "-")))
            table.add_row(
                "included_doc_paths", str(
                    fileconfig.get("included_doc_paths", "-"))
            )
            table.add_row(
                "excluded_doc_paths", str(
                    fileconfig.get("excluded_doc_paths", "-"))
            )
            table.add_row(
                "config_parameter", str(
                    fileconfig.get("config_parameter", "-"))
            )
            table.add_row("depth", str(fileconfig.get("depth", "-")))
            table.add_row(
                "max_access_count", str(
                    fileconfig.get("max_access_count", "-"))
            )
            table.add_row("num_of_thread", str(
                fileconfig.get("num_of_thread", "-")))
            table.add_row("interval_time", str(
                fileconfig.get("interval_time", "-")))
            table.add_row("boost", str(fileconfig.get("boost", "-")))
            table.add_row("available", str(fileconfig.get("available", "-")))
            table.add_row("permissions", str(
                fileconfig.get("permissions", "-")))
            table.add_row("virtual_hosts", str(
                fileconfig.get("virtual_hosts", "-")))
            table.add_row("sort_order", str(fileconfig.get("sort_order", "-")))
            table.add_row("created_by", str(fileconfig.get("created_by", "-")))
            table.add_row("created_time", str(
                fileconfig.get("created_time", "-")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve FileConfig. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@fileconfig_app.command("list")
def list_fileconfigs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    List FileConfigs.
    """
    client = FessAPIClient()
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
                typer.secho("No FileConfigs found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="FileConfigs")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="cyan", no_wrap=True)
                for config in configs:
                    table.add_row(config.get("id", "-"),
                                  config.get("name", "-"))
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list FileConfigs. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


def _handle_response(result: dict, output: str, success_message: Optional[str] = None):
    """
    Handle API response output.
    """
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            if success_message:
                typer.secho(success_message, fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Operation failed. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
