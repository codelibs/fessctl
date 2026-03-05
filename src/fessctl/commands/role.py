import datetime
import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import encode_to_urlsafe_base64, format_detail_markdown, format_list_markdown, format_result_markdown, output_error

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
    ),
):
    """
    Create a new role in Fess.
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
        result = client.create_role(name=name, attributes=attr_dict)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                role_id = result.get("response", {}).get("id", None)
                typer.echo(format_result_markdown(True, f"Role '{name}' created successfully with ID: {role_id}.", "Role", "create", role_id or ""))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to create role. {message} Status code: {status}", "Role", "create"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Role", "create")
        raise typer.Exit(code=1)


@role_app.command("update")
def update_role(
    role_id: str = typer.Argument(..., help="ID of the role to update"),
    attributes: Optional[List[str]] = typer.Option(
        None, "--attribute", "-a", help="Attributes in key=value format"
    ),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Update an existing role.
    """
    client = FessAPIClient(Settings())

    result = client.get_role(role_id=role_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"Role with ID '{role_id}' not found. {message}", "Role", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

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

    result = client.update_role(config)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"Role '{role_id}' updated successfully.", "Role", "update", role_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update role. {message} Status code: {status}", "Role", "update"))
            raise typer.Exit(code=status)


@role_app.command("delete")
def delete_role(
    role_id: str = typer.Argument(..., help="ID of the role to delete"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Delete a role in Fess.
    """
    client = FessAPIClient(Settings())

    try:
        result = client.delete_role(role_id=role_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                typer.echo(format_result_markdown(True, f"Role with ID '{role_id}' deleted successfully.", "Role", "delete", role_id))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to delete role. {message} Status code: {status}", "Role", "delete"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Role", "delete")
        raise typer.Exit(code=1)


@role_app.command("getbyname")
def get_role_by_name(
    name: str = typer.Argument(..., help="Name of the role to retrieve"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    get_role(encode_to_urlsafe_base64(name), output=output)


@role_app.command("get")
def get_role(
    role_id: str = typer.Argument(..., help="ID of the role to retrieve"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    Retrieve details of a specific role in Fess.
    """
    client = FessAPIClient(Settings())

    try:
        result = client.get_role(role_id=role_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                role = result.get("response", {}).get("setting", {})
                attributes = role.get("attributes", {})
                attr_str = (
                    "\n".join(f"{k}={v}" for k, v in attributes.items())
                    if attributes
                    else "-"
                )
                data = dict(role)
                data["attributes_display"] = attr_str
                typer.echo(format_detail_markdown(
                    f"Role Details: {role.get('name', '-')}",
                    data,
                    [
                        ("ID", "id"),
                        ("Name", "name"),
                        ("Attributes", "attributes_display"),
                        ("Version", "version_no"),
                    ],
                ))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to retrieve role. {message} Status code: {status}", "Role", "get"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Role", "get")
        raise typer.Exit(code=1)


@role_app.command("list")
def list_roles(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    """
    List roles in Fess.
    """
    client = FessAPIClient(Settings())

    try:
        result = client.list_roles(page=page, size=size)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                roles = result.get("response", {}).get("settings", [])
                if not roles:
                    typer.echo("No roles found.")
                else:
                    display_items = []
                    for item in roles:
                        d = dict(item)
                        d["attributes_display"] = "\n".join(
                            f"{k}={v}"
                            for k, v in item.get("attributes", {}).items()
                        )
                        display_items.append(d)
                    typer.echo(format_list_markdown("Roles", display_items, [
                        ("ID", "id"),
                        ("NAME", "name"),
                        ("ATTRIBUTES", "attributes_display"),
                        ("VERSION", "version_no"),
                    ]))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to list roles. {message} Status code: {status}", "Role", "list"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Role", "list")
        raise typer.Exit(code=1)
