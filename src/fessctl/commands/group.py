import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient

# Create a Typer sub-application for group commands
group_app = typer.Typer()


@group_app.command("create")
def create_group(
    name: str = typer.Argument(..., help="Group name (max 100 characters)"),
    attributes: Optional[List[str]] = typer.Option(
        None,
        "--attribute",
        "-a",
        help="Group attributes in key=value format. Can be specified multiple times.",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Create a new group in Fess.
    """
    client = FessAPIClient()
    attr_dict = {}
    if attributes:
        for attr in attributes:
            if "=" not in attr:
                typer.secho(f"Invalid attribute format: {attr}", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            key, value = attr.split("=", 1)
            attr_dict[key.strip()] = value.strip()

    try:
        result = client.create_group(name=name, attributes=attr_dict)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                group_id = result.get("response", {}).get("id", None)
                typer.secho(
                    f"Group '{name}' created successfully with ID: {group_id}.",
                    fg=typer.colors.GREEN,
                )
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to create group. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error creating group: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@group_app.command("delete")
def delete_group(
    group_id: str = typer.Argument(..., help="ID of the group to delete"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Delete a group in Fess.
    """
    client = FessAPIClient()

    try:
        result = client.delete_group(group_id=group_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                typer.secho(
                    f"Group with ID '{group_id}' deleted successfully.",
                    fg=typer.colors.GREEN,
                )
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to delete group. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error deleting group: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@group_app.command("get")
def get_group(
    group_id: str = typer.Argument(..., help="ID of the group to retrieve"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Retrieve details of a specific group in Fess.
    """
    client = FessAPIClient()

    try:
        result = client.get_group(group_id=group_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                group = result.get("response", {}).get("setting", {})
                console = Console()
                table = Table(title=f"Group Details: {group.get('name', '-')}")
                table.add_column("Field", style="cyan", no_wrap=True)
                table.add_column("Value", style="magenta")

                table.add_row("ID", group.get("id", "-"))
                table.add_row("Name", group.get("name", "-"))
                attributes = group.get("attributes", {})
                attr_str = (
                    "\n".join(f"{k}={v}" for k, v in attributes.items())
                    if attributes
                    else "-"
                )
                table.add_row("Attributes", attr_str)
                table.add_row("Version", str(group.get("version_no", "-")))

                console.print(table)
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to retrieve group. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error retrieving group: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@group_app.command("list")
def list_groups(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    List groups in Fess.
    """
    client = FessAPIClient()

    try:
        result = client.list_groups(page=page, size=size)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                groups = result.get("response", {}).get("settings", [])
                if not groups:
                    typer.secho("No groups found.", fg=typer.colors.YELLOW)
                else:
                    console = Console()
                    table = Table(title="Groups")
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("NAME", style="cyan", no_wrap=True)
                    table.add_column("ATTRIBUTES", style="cyan", no_wrap=False)
                    table.add_column("VERSION", style="cyan", no_wrap=True)
                    for group in groups:
                        table.add_row(
                            *[
                                group.get("id", "-"),
                                group.get("name", "-"),
                                "\n".join(
                                    f"{k}={v}"
                                    for k, v in group.get("attributes", {}).items()
                                ),
                                str(group.get("version_no", "-")),
                            ]
                        )
                    console.print(table)
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to list groups. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error listing groups: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
