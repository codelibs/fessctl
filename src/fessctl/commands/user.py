import datetime
import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import encode_to_urlsafe_base64, format_detail_markdown, format_list_markdown, format_result_markdown, output_error

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
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                user_id = result.get("response", {}).get("id", None)
                typer.echo(format_result_markdown(True, f"User '{name}' created successfully with ID: {user_id}.", "User", "create", user_id or ""))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to create user. {message} Status code: {status}", "User", "create"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "User", "create")
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
        typer.echo(format_result_markdown(False, f"User with ID '{user_id}' not found. {message}", "User", "update"))
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
            typer.echo(format_result_markdown(True, f"User '{user_id}' updated successfully.", "User", "update", user_id))
        else:
            message: str = update_resp.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update user. {message} Status code: {status}", "User", "update"))
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
                typer.echo(format_result_markdown(True, f"User with ID '{user_id}' deleted successfully.", "User", "delete", user_id))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to delete user. {message} Status code: {status}", "User", "delete"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "User", "delete")
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
                data = dict(user_info)
                data["roles_display"] = "\n".join(user_info.get("roles", []))
                data["groups_display"] = "\n".join(user_info.get("groups", []))
                attrs = user_info.get("attributes", {})
                if isinstance(attrs, dict):
                    data["attributes_display"] = "\n".join(f"{k}={v}" for k, v in attrs.items())
                else:
                    data["attributes_display"] = "\n".join(str(a) for a in attrs)
                typer.echo(format_detail_markdown(
                    f"User Details: {user_info.get('name', '-')}",
                    data,
                    [
                        ("ID", "id"),
                        ("Name", "name"),
                        ("Roles", "roles_display"),
                        ("Groups", "groups_display"),
                        ("Attributes", "attributes_display"),
                        ("Version", "version_no"),
                    ],
                ))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to retrieve user. {message} Status code: {status}", "User", "get"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "User", "get")
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
                    typer.echo("No web authentication users found.")
                else:
                    display_items = []
                    for item in users:
                        d = dict(item)
                        d["roles_display"] = "\n".join(item.get("roles", []))
                        d["groups_display"] = "\n".join(item.get("groups", []))
                        d["attributes_display"] = "\n".join(
                            f"{k}={v}"
                            for k, v in item.get("attributes", {}).items()
                        )
                        display_items.append(d)
                    typer.echo(format_list_markdown("Web Authentication Users", display_items, [
                        ("ID", "id"),
                        ("NAME", "name"),
                        ("ROLES", "roles_display"),
                        ("GROUPS", "groups_display"),
                        ("ATTRIBUTES", "attributes_display"),
                        ("VERSION", "version_no"),
                    ]))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to list web authentication users. {message} Status code: {status}", "User", "list"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "User", "list")
        raise typer.Exit(code=1)
