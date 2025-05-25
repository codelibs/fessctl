import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import to_utc_iso8601

labeltype_app = typer.Typer()


@labeltype_app.command("create")
def create_labeltype(
    name: str = typer.Option(..., "--name", help="LabelType name"),
    value: str = typer.Option(..., "--value", help="Label value"),
    version_no: int = typer.Option(..., "--version-no", help="Version number"),
    sort_order: int = typer.Option(0, "--sort-order", help="Sort order"),
    included_paths: Optional[List[str]] = typer.Option(
        [], "--included-path", help="Included paths"),
    excluded_paths: Optional[List[str]] = typer.Option(
        [], "--excluded-path", help="Excluded paths"),
    permissions: Optional[List[str]] = typer.Option(
        [], "--permission", help="Access permissions"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host"),
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
    Create a new LabelType.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "name": name,
        "value": value,
        "version_no": version_no,
        "sort_order": sort_order,
        "created_by": created_by,
        "created_time": created_time,
    }

    if included_paths:
        config["included_paths"] = "\n".join(included_paths)
    if excluded_paths:
        config["excluded_paths"] = "\n".join(excluded_paths)
    if permissions:
        config["permissions"] = "\n".join(permissions)
    if virtual_host:
        config["virtual_host"] = virtual_host

    result = client.create_labeltype(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            labeltype_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"LabelType '{labeltype_id}' created successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create LabelType. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@labeltype_app.command("update")
def update_labeltype(
    config_id: str = typer.Argument(..., help="LabelType ID"),
    name: Optional[str] = typer.Option(None, "--name", help="LabelType name"),
    value: Optional[str] = typer.Option(None, "--value", help="Label value"),
    version_no: Optional[int] = typer.Option(
        None, "--version-no", help="Version number"),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    included_paths: Optional[List[str]] = typer.Option(
        None, "--included-path", help="Included paths"),
    excluded_paths: Optional[List[str]] = typer.Option(
        None, "--excluded-path", help="Excluded paths"),
    permissions: Optional[List[str]] = typer.Option(
        None, "--permission", help="Access permissions"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Update an existing LabelType.
    """
    client = FessAPIClient(Settings())
    result = client.get_labeltype(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"LabelType with ID '{config_id}' not found. {message}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if name is not None:
        config["name"] = name
    if value is not None:
        config["value"] = value
    if version_no is not None:
        config["version_no"] = version_no
    if sort_order is not None:
        config["sort_order"] = sort_order
    if included_paths is not None:
        config["included_paths"] = "\n".join(included_paths)
    if excluded_paths is not None:
        config["excluded_paths"] = "\n".join(excluded_paths)
    if permissions is not None:
        config["permissions"] = "\n".join(permissions)
    if virtual_host is not None:
        config["virtual_host"] = virtual_host

    result = client.update_labeltype(config)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"LabelType '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update LabelType. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@labeltype_app.command("delete")
def delete_labeltype(
    config_id: str = typer.Argument(..., help="LabelType ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a LabelType by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_labeltype(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"LabelType '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete LabelType. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@labeltype_app.command("get")
def get_labeltype(
    config_id: str = typer.Argument(..., help="LabelType ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a LabelType by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_labeltype(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            labeltype = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(
                title=f"LabelType Details: {labeltype.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row("id", str(labeltype.get("id", "-")))
            table.add_row("name", str(labeltype.get("name", "-")))
            table.add_row("value", str(labeltype.get("value", "-")))
            table.add_row("version_no", str(labeltype.get("version_no", "-")))
            table.add_row("sort_order", str(labeltype.get("sort_order", "-")))
            table.add_row("included_paths", labeltype.get(
                "included_paths", "").replace("\n", ", "))
            table.add_row("excluded_paths", labeltype.get(
                "excluded_paths", "").replace("\n", ", "))
            table.add_row("permissions", labeltype.get(
                "permissions", "").replace("\n", ", "))
            table.add_row("virtual_host", str(
                labeltype.get("virtual_host", "-")))
            table.add_row("crud_mode", str(labeltype.get("crud_mode", "-")))
            table.add_row("created_by", str(labeltype.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                labeltype.get("created_time")))
            table.add_row("updated_by", str(labeltype.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                labeltype.get("updated_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve LabelType. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@labeltype_app.command("list")
def list_labeltypes(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List LabelTypes.
    """
    client = FessAPIClient(Settings())
    result = client.list_labeltypes(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            labeltypes = result.get("response", {}).get("settings", [])
            if not labeltypes:
                typer.secho("No LabelTypes found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="LabelTypes")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("NAME", style="green")
                table.add_column("VALUE", style="magenta")

                for lt in labeltypes:
                    table.add_row(
                        lt.get("id", "-"),
                        lt.get("name", "-"),
                        lt.get("value", "-"),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list LabelTypes. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
