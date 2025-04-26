import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient

# Create a Typer sub-application for role commands
user_app = typer.Typer()


@user_app.command("create")
def create_user_command(
    name: str = typer.Argument(..., help="Username (max 100 characters)"),
    password: str = typer.Argument(..., help="Password (max 100 characters)"),
    attributes: Optional[List[str]] = typer.Option(
        None,
        "--attribute",
        "-a",
        help="User attributes in key=value format. Can be specified multiple times.",
    ),
    roles: Optional[List[str]] = typer.Option(
        None,
        "--role",
        "-r",
        help="Roles to assign to the user. Can be specified multiple times.",
    ),
    groups: Optional[List[str]] = typer.Option(
        None,
        "--group",
        "-g",
        help="Groups to assign to the user. Can be specified multiple times.",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Create a new user in Fess.
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
        result = client.create_user(
            name=name,
            password=password,
            confirm_password=password,
            attributes=attr_dict if attr_dict else None,
            roles=roles,
            groups=groups,
        )
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            import yaml

            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                user_id = result.get("response", {}).get("id", None)
                typer.secho(
                    f"User '{name}' created successfully with ID: {user_id}.",
                    fg=typer.colors.GREEN,
                )
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to create user. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error creating user: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@user_app.command("delete")
def delete_user_command(
    user_id: str = typer.Argument(..., help="ID of the user to delete"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Delete a user from Fess.
    """
    client = FessAPIClient()
    try:
        result = client.delete_user(user_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                typer.secho(
                    f"User with ID '{user_id}' deleted successfully.",
                    fg=typer.colors.GREEN,
                )
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to delete user. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error deleting user: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@user_app.command("get")
def get_user_command(
    user_id: str = typer.Argument(..., help="ID of the user to retrieve"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Retrieve details of a user from Fess.
    """
    client = FessAPIClient()
    try:
        result = client.get_user(user_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                user_info = result.get("response", {}).get("setting", {})
                console = Console()
                table = Table(title=f"User Details: {user_info.get('name', '-')}")
                table.add_column("Field", style="cyan", no_wrap=True)
                table.add_column("Value", style="magenta")

                table.add_row("ID", user_info.get("id", "-"))
                table.add_row("Name", user_info.get("name", "-"))
                table.add_row("Roles", "\n".join(user_info.get("roles", [])))
                table.add_row("Groups", "\n".join(user_info.get("groups", [])))
                table.add_row("Attributes", "\n".join(user_info.get("attributes", [])))
                table.add_row("Version", str(user_info.get("version_no", "-")))
                console.print(table)
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to retrieve user. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error retrieving user: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@user_app.command("list")
def list_users_command(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    List web authentication users in Fess.
    """
    client = FessAPIClient()

    try:
        result = client.list_users(page=page, size=size)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                users = result.get("response", {}).get("settings", [])
                if not users:
                    typer.secho(
                        "No web authentication users found.", fg=typer.colors.YELLOW
                    )
                else:
                    console = Console()
                    table = Table(title="Web Authentication Users")
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("NAME", style="cyan", no_wrap=True)
                    table.add_column("ROLES", style="cyan", no_wrap=False)
                    table.add_column("GROUPS", style="cyan", no_wrap=False)
                    table.add_column("ATTRIBUTES", style="cyan", no_wrap=False)
                    table.add_column("VERSION", style="cyan", no_wrap=True)
                    for user in users:
                        table.add_row(
                            user.get("id", "-"),
                            user.get("name", "-"),
                            "\n".join(user.get("roles", [])),
                            "\n".join(user.get("groups", [])),
                            "\n".join(
                                f"{k}={v}"
                                for k, v in user.get("attributes", {}).items()
                            ),
                            str(user.get("version_no", "-")),
                        )
                    console.print(table)
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Failed to list web authentication users. {message} Status code: {status}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(f"Error listing web authentication users: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
