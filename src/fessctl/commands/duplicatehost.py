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
            typer.secho(
                f"DuplicateHost '{dup_id}' created successfully.", fg=typer.colors.GREEN
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create DuplicateHost. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
        typer.secho(
            f"DuplicateHost with ID '{config_id}' not found. {message}",
            fg=typer.colors.RED,
        )
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
            typer.secho(
                f"DuplicateHost '{config_id}' updated successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update DuplicateHost. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
            typer.secho(
                f"DuplicateHost '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete DuplicateHost. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
            console = Console()
            table = Table(
                title=f"DuplicateHost Details: {duplicatehost.get('id', '-')}"
            )
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # 正しい public name ベースのフィールドのみを表示
            table.add_row("id", str(duplicatehost.get("id", "-")))
            table.add_row("regular_name", str(
                duplicatehost.get("regular_name", "-")))
            table.add_row(
                "duplicate_host_name",
                str(duplicatehost.get("duplicate_host_name", "-")),
            )
            table.add_row("sort_order", str(
                duplicatehost.get("sort_order", "-")))
            table.add_row("version_no", str(
                duplicatehost.get("version_no", "-")))
            table.add_row("crud_mode", str(
                duplicatehost.get("crud_mode", "-")))
            table.add_row("updated_by", str(
                duplicatehost.get("updated_by", "-")))
            table.add_row(
                "updated_time", to_utc_iso8601(
                    duplicatehost.get("updated_time"))
            )
            table.add_row("created_by", str(
                duplicatehost.get("created_by", "-")))
            table.add_row(
                "created_time", to_utc_iso8601(
                    duplicatehost.get("created_time"))
            )

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve DuplicateHost. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
                typer.secho("No DuplicateHosts found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="DuplicateHosts")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("REGULAR NAME", style="magenta")
                table.add_column("DUPLICATE HOST NAME", style="green")
                table.add_column("SORT ORDER", style="yellow")
                table.add_column("UPDATED BY", style="blue")
                table.add_column("UPDATED TIME", style="white")

                for dh in duplicatehosts:
                    table.add_row(
                        dh.get("id", "-"),
                        dh.get("regular_name", "-"),
                        dh.get("duplicate_host_name", "-"),
                        str(dh.get("sort_order", "-")),
                        dh.get("updated_by", "-"),
                        to_utc_iso8601(dh.get("updated_time")),
                    )
                console.print(table)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list DuplicateHosts. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
