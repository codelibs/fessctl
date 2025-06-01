import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import encode_to_urlsafe_base64

# Create a Typer sub-application for role commands
user_app = typer.Typer()


@user_app.command("create")
def create_user(
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
    client = FessAPIClient(Settings())
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


@user_app.command("update")
def update_user(
    user_id: str = typer.Argument(..., help="ID of the user to update"),
    password: Optional[str] = typer.Option(
        None, "--password", "-p", help="Password (max 100 characters)"
    ),
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
    Update an existing user in Fess.
    """
    client = FessAPIClient(Settings())

    # 1) Fetch existing user
    result = client.get_user(user_id)
    status = result.get("response", {}).get("status", 1)
    if status != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"User with ID '{user_id}' not found. {message}", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)

    # 2) Merge existing setting into config
    config = result["response"].get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    # 3) Override with provided options
    if attributes is not None:
        attr_dict = {}
        for attr in attributes:
            if "=" not in attr:
                typer.secho(
                    f"Invalid attribute format: {attr}", fg=typer.colors.RED)
                raise typer.Exit(code=1)
            key, value = attr.split("=", 1)
            attr_dict[key.strip()] = value.strip()
        config["attributes"] = attr_dict

    if password is not None:
        if len(password) > 100:
            typer.secho(
                "Password must be 100 characters or less.", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        config["password"] = password
        config["confirm_password"] = password

    if roles is not None:
        config["roles"] = roles

    if groups is not None:
        config["groups"] = groups

    # 4) Send update request
    update_resp = client.update_user(config)
    status = update_resp.get("response", {}).get("status", 1)

    # 5) Render output
    if output == "json":
        typer.echo(json.dumps(update_resp, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(update_resp))
    else:
        if status == 0:
            typer.secho(
                f"User '{user_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message: str = update_resp.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update user. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@user_app.command("delete")
def delete_user(
    user_id: str = typer.Argument(..., help="ID of the user to delete"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Delete a user from Fess.
    """
    client = FessAPIClient(Settings())
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


@user_app.command("getbyname")
def get_user_by_name(
    name: str = typer.Argument(..., help="Name of the user to retrieve"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    get_user(encode_to_urlsafe_base64(name), output=output)


@user_app.command("get")
def get_user(
    user_id: str = typer.Argument(..., help="ID of the user to retrieve"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Retrieve details of a user from Fess.
    """
    client = FessAPIClient(Settings())
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
                table = Table(
                    title=f"User Details: {user_info.get('name', '-')}")
                table.add_column("Field", style="cyan", no_wrap=True)
                table.add_column("Value", style="magenta")

                table.add_row("ID", user_info.get("id", "-"))
                table.add_row("Name", user_info.get("name", "-"))
                table.add_row("Roles", "\n".join(user_info.get("roles", [])))
                table.add_row("Groups", "\n".join(user_info.get("groups", [])))
                table.add_row("Attributes", "\n".join(
                    user_info.get("attributes", [])))
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
def list_users(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    List web authentication users in Fess.
    """
    client = FessAPIClient(Settings())

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
        typer.secho(
            f"Error listing web authentication users: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
