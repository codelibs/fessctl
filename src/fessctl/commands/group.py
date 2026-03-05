import datetime
import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import encode_to_urlsafe_base64, format_detail_markdown, format_list_markdown, format_result_markdown, output_error


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
        result = client.create_group(name=name, attributes=attr_dict)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                group_id = result.get("response", {}).get("id", None)
                typer.echo(format_result_markdown(True, f"Group '{name}' created successfully with ID: {group_id}.", "Group", "create", group_id or ""))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to create group. {message} Status code: {status}", "Group", "create"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Group", "create")
        raise typer.Exit(code=1)


@group_app.command("update")
def update_group(
    group_id: str = typer.Argument(..., help="ID of the group to update"),
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
    Update an existing group.
    """
    client = FessAPIClient(Settings())

    try:
        result = client.get_group(group_id=group_id)
        if result.get("response", {}).get("status", 1) != 0:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Group with ID '{group_id}' not found. {message}", "Group", "update"))
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

        result = client.update_group(config)
        status = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                typer.echo(format_result_markdown(True, f"Group '{group_id}' updated successfully.", "Group", "update", group_id))
            else:
                message = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to update group. {message} Status code: {status}", "Group", "update"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Group", "update")
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
    client = FessAPIClient(Settings())

    try:
        result = client.delete_group(group_id=group_id)
        status: int = result.get("response", {}).get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == 0:
                typer.echo(format_result_markdown(True, f"Group with ID '{group_id}' deleted successfully.", "Group", "delete", group_id))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to delete group. {message} Status code: {status}", "Group", "delete"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Group", "delete")
        raise typer.Exit(code=1)


@group_app.command("getbyname")
def get_group_by_name(
    name: str = typer.Argument(..., help="Name of the group to retrieve"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    ),
):
    get_group(encode_to_urlsafe_base64(name), output=output)


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
    client = FessAPIClient(Settings())

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
                attributes = group.get("attributes", {})
                attr_str = (
                    "\n".join(f"{k}={v}" for k, v in attributes.items())
                    if attributes
                    else "-"
                )
                data = dict(group)
                data["attributes_display"] = attr_str
                typer.echo(format_detail_markdown(
                    f"Group Details: {group.get('name', '-')}",
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
                typer.echo(format_result_markdown(False, f"Failed to retrieve group. {message} Status code: {status}", "Group", "get"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Group", "get")
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
    client = FessAPIClient(Settings())

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
                    typer.echo("No groups found.")
                else:
                    display_items = []
                    for item in groups:
                        d = dict(item)
                        d["attributes_display"] = "\n".join(
                            f"{k}={v}"
                            for k, v in item.get("attributes", {}).items()
                        )
                        display_items.append(d)
                    typer.echo(format_list_markdown("Groups", display_items, [
                        ("ID", "id"),
                        ("NAME", "name"),
                        ("ATTRIBUTES", "attributes_display"),
                        ("VERSION", "version_no"),
                    ]))
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.echo(format_result_markdown(False, f"Failed to list groups. {message} Status code: {status}", "Group", "list"))
                raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Group", "list")
        raise typer.Exit(code=1)
