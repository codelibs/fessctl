import json
from typing import List, Optional
from rich.table import Table
from rich.console import Console
import typer

from fessctl.api.client import FessAPIClient

# Create a Typer sub-application for role commands
role_app = typer.Typer()


@role_app.command("create")
def create_role(
    name: str = typer.Argument(..., help="Role name (max 100 characters)"),
    attributes: Optional[List[str]] = typer.Option(
        None,
        "--attribute",
        "-a",
        help="Role attributes in key=value format. Can be specified multiple times.",
    ),
        output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    )
):
    """
    Create a new role in Fess.
    """
    client = FessAPIClient()
    attr_dict = {}
    if attributes:
        for attr in attributes:
            if "=" not in attr:
                typer.secho(
                    f"Invalid attribute format: {attr}", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            key, value = attr.split("=", 1)
            attr_dict[key.strip()] = value.strip()

    try:
        result = client.create_role(name=name, attributes=attr_dict)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            import yaml
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                role_id = result.get("response", {}).get("id", None)
                typer.secho(
                    f"Role '{name}' created successfully with ID: {role_id}.", fg=typer.colors.GREEN)
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to create role. {message} Status code: {status}", fg=typer.colors.RED)
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error creating role: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@role_app.command("delete")
def delete_role(
    role_id: str = typer.Argument(..., help="ID of the role to delete"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml")
):
    """
    Delete a role in Fess.
    """
    client = FessAPIClient()

    try:
        result = client.delete_role(role_id=role_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            import yaml
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                typer.secho(
                    f"Role with ID '{role_id}' deleted successfully.", fg=typer.colors.GREEN)
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to delete role. {message} Status code: {status}", fg=typer.colors.RED)
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error deleting role: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@role_app.command("list")
def list_roles(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml")
):
    """
    List roles in Fess.
    """
    client = FessAPIClient()

    try:
        result = client.list_roles(page=page, size=size)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            import yaml
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                roles = result.get("response", {}).get("settings", [])
                if not roles:
                    typer.secho("No roles found.", fg=typer.colors.YELLOW)
                else:
                    console = Console()
                    table = Table(title="Roles")
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("NAME", style="cyan", no_wrap=True)
                    table.add_column("ATTRIBUTES", style="cyan", no_wrap=False)
                    table.add_column("VERSION", style="cyan", no_wrap=True)
                    for role in roles:
                        table.add_row(*[role.get("id", "-"),
                                        role.get("name", "-"),
                                        ", ".join(f"{k}={v}" for k, v in role.get(
                                            "attributes", {}).items()),
                                        str(role.get("version_no", "-")),
                                        ])
                    console.print(table)
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to list roles. {message} Status code: {status}", fg=typer.colors.RED)
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error listing roles: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
