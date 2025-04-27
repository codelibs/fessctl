from typing import List
import datetime
import json
import typer
import yaml
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from fessctl.api.client import FessAPIClient

dataconfig_app = typer.Typer()


@dataconfig_app.command("create")
def create_dataconfig(
    name: str = typer.Option(..., "--name", help="DataConfig name"),
    handler_name: str = typer.Option(...,
                                     "--handler-name", help="Handler name"),
    boost: float = typer.Option(1.0, "--boost", help="Boost value"),
    available: bool = typer.Option(
        True, "--available", help="Availability (true/false)"),
    sort_order: int = typer.Option(1, "--sort-order", help="Sort order"),
    description: str = typer.Option("", "--description", help="Description"),
    handler_parameter: str = typer.Option(
        "", "--handler-parameter", help="Handler parameters"),
    handler_script: str = typer.Option(
        "", "--handler-script", help="Handler script"),
    permissions: List[str] = typer.Option(
        ["{role}guest"], "--permission", help="Access permissions"),
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
    Create a new DataConfig.
    """
    client = FessAPIClient()

    config = {
        "crud_mode": 1,
        "name": name,
        "handler_name": handler_name,
        "boost": boost,
        "available": "true" if available else "false",
        "sort_order": sort_order,
        "description": description,
        "handler_parameter": handler_parameter,
        "handler_script": handler_script,
        "permissions": "\n".join(permissions),
        "virtual_hosts": "\n".join(virtual_hosts),
        "created_by": created_by,
        "created_time": created_time,
    }

    result = client.create_dataconfig(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            config_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"DataConfig '{config_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Operation failed. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@dataconfig_app.command("update")
def update_dataconfig(
    config_id: str = typer.Argument(..., help="DataConfig ID"),
    name: Optional[str] = typer.Option(None, "--name", help="DataConfig name"),
    handler_name: Optional[str] = typer.Option(
        None, "--handler-name", help="Handler name"),
    boost: Optional[float] = typer.Option(None, "--boost", help="Boost value"),
    available: Optional[bool] = typer.Option(
        None, "--available", help="Availability (true/false)"),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Description"),
    handler_parameter: Optional[str] = typer.Option(
        None, "--handler-parameter", help="Handler parameters"),
    handler_script: Optional[str] = typer.Option(
        None, "--handler-script", help="Handler script"),
    permissions: Optional[List[str]] = typer.Option(
        None, "--permission", help="Access permissions"),
    virtual_hosts: Optional[List[str]] = typer.Option(
        None, "--virtual-host", help="Virtual hosts"),
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
    Update an existing DataConfig.
    """
    client = FessAPIClient()
    result = client.get_dataconfig(config_id)

    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"DataConfig with ID '{config_id}' not found. {message}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if name is not None:
        config["name"] = name
    if handler_name is not None:
        config["handler_name"] = handler_name
    if boost is not None:
        config["boost"] = boost
    if available is not None:
        config["available"] = available
    if sort_order is not None:
        config["sort_order"] = sort_order
    if description is not None:
        config["description"] = description
    if handler_parameter is not None:
        config["handler_parameter"] = handler_parameter
    if handler_script is not None:
        config["handler_script"] = handler_script
    if permissions is not None:
        config["permissions"] = "\n".join(permissions)
    if virtual_hosts is not None:
        config["virtual_hosts"] = "\n".join(virtual_hosts)

    result = client.update_dataconfig(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            config_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"DataConfig '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Operation failed. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@dataconfig_app.command("delete")
def delete_dataconfig(
    config_id: str = typer.Argument(..., help="DataConfig ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a DataConfig by ID.
    """
    client = FessAPIClient()
    result = client.delete_dataconfig(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"DataConfig '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete DataConfig. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@dataconfig_app.command("get")
def get_dataconfig(
    config_id: str = typer.Argument(..., help="DataConfig ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Retrieve a DataConfig by ID.
    """
    client = FessAPIClient()
    result = client.get_dataconfig(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            dataconfig = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(
                title=f"DataConfig Details: {dataconfig.get('name', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row("id", str(dataconfig.get("id", "-")))
            table.add_row("updated_by", str(dataconfig.get("updated_by", "-")))
            table.add_row("updated_time", str(
                dataconfig.get("updated_time", "-")))
            table.add_row("version_no", str(dataconfig.get("version_no", "-")))
            table.add_row("crud_mode", str(dataconfig.get("crud_mode", "-")))
            table.add_row("name", str(dataconfig.get("name", "-")))
            table.add_row("description", str(
                dataconfig.get("description", "-")))
            table.add_row("handler_name", str(
                dataconfig.get("handler_name", "-")))
            table.add_row("handler_parameter", str(
                dataconfig.get("handler_parameter", "-")))
            table.add_row("handler_script", str(
                dataconfig.get("handler_script", "-")))
            table.add_row("boost", str(dataconfig.get("boost", "-")))
            table.add_row("available", str(dataconfig.get("available", "-")))
            table.add_row("permissions", str(
                dataconfig.get("permissions", "-")))
            table.add_row("virtual_hosts", str(
                dataconfig.get("virtual_hosts", "-")))
            table.add_row("sort_order", str(dataconfig.get("sort_order", "-")))
            table.add_row("created_by", str(dataconfig.get("created_by", "-")))
            table.add_row("created_time", str(
                dataconfig.get("created_time", "-")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve DataConfig. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@dataconfig_app.command("list")
def list_dataconfigs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List DataConfigs.
    """
    client = FessAPIClient()
    result = client.list_dataconfigs(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            dataconfigs = result.get("response", {}).get("settings", [])
            if not dataconfigs:
                typer.secho("No DataConfigs found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="DataConfigs")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("NAME", style="cyan", no_wrap=True)
                table.add_column("AVAILABLE", style="cyan", no_wrap=True)
                table.add_column("SORT ORDER", style="cyan", no_wrap=True)
                for dataconfig in dataconfigs:
                    table.add_row(
                        dataconfig.get("id", "-"),
                        dataconfig.get("name", "-"),
                        dataconfig.get("available", "-"),
                        str(dataconfig.get("sort_order", "-")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list DataConfigs. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
