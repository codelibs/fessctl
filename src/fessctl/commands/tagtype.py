import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import (
    format_detail_markdown,
    format_list_markdown,
    format_result_markdown,
)

tagtype_app = typer.Typer()


@tagtype_app.command("create")
def create_tagtype(
    name: str = typer.Option(..., "--name", help="Tag name"),
    owner: str = typer.Option(..., "--owner", help="User who owns the tag"),
    sort_order: int = typer.Option(0, "--sort-order", help="Sort order"),
    paths: Optional[List[str]] = typer.Option(
        [], "--path", help="URL of a tagged document"),
    permissions: Optional[List[str]] = typer.Option(
        [], "--permission", help="Access permissions"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new TagType.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "name": name,
        "owner": owner,
        "sort_order": sort_order,
    }

    if paths:
        config["paths"] = "\n".join(paths)
    if permissions:
        config["permissions"] = "\n".join(permissions)
    if virtual_host:
        config["virtual_host"] = virtual_host

    result = client.create_tagtype(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            tagtype_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"TagType '{tagtype_id}' created successfully.", "TagType", "create", tagtype_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create TagType. {message} Status code: {status}", "TagType", "create"))
            raise typer.Exit(code=status)


@tagtype_app.command("update")
def update_tagtype(
    config_id: str = typer.Argument(..., help="TagType ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Tag name"),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="User who owns the tag"),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    paths: Optional[List[str]] = typer.Option(
        None, "--path", help="URL of a tagged document"),
    permissions: Optional[List[str]] = typer.Option(
        None, "--permission", help="Access permissions"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Update an existing TagType. Changing the name or the owner gives it a new ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_tagtype(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"TagType with ID '{config_id}' not found. {message}", "TagType", "update"))
        raise typer.Exit(code=1)

    # The PUT replaces the whole tag, so start from the current one (including
    # its paths, seq_no and primary_term) and override only the given fields.
    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2

    if name is not None:
        config["name"] = name
    if owner is not None:
        config["owner"] = owner
    if sort_order is not None:
        config["sort_order"] = sort_order
    if paths is not None:
        config["paths"] = "\n".join(paths)
    if permissions is not None:
        config["permissions"] = "\n".join(permissions)
    if virtual_host is not None:
        config["virtual_host"] = virtual_host

    result = client.update_tagtype(config)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            tagtype_id = result.get("response", {}).get("id") or config_id
            typer.echo(format_result_markdown(True, f"TagType '{tagtype_id}' updated successfully.", "TagType", "update", tagtype_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update TagType. {message} Status code: {status}", "TagType", "update"))
            raise typer.Exit(code=status)


@tagtype_app.command("delete")
def delete_tagtype(
    config_id: str = typer.Argument(..., help="TagType ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a TagType by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_tagtype(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"TagType '{config_id}' deleted successfully.", "TagType", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete TagType. {message} Status code: {status}", "TagType", "delete"))
            raise typer.Exit(code=status)


@tagtype_app.command("get")
def get_tagtype(
    config_id: str = typer.Argument(..., help="TagType ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a TagType by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_tagtype(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            tagtype = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"TagType Details: {tagtype.get('id', '-')}",
                tagtype,
                [
                    ("id", "id"),
                    ("name", "name"),
                    ("owner", "owner"),
                    ("sort_order", "sort_order"),
                    ("paths", "paths"),
                    ("permissions", "permissions"),
                    ("virtual_host", "virtual_host"),
                    ("seq_no", "seq_no"),
                    ("primary_term", "primary_term"),
                ],
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve TagType. {message} Status code: {status}", "TagType", "get"))
            raise typer.Exit(code=status)


@tagtype_app.command("list")
def list_tagtypes(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List TagTypes. The paths of each tag are left out; use get to see them.
    """
    client = FessAPIClient(Settings())
    result = client.list_tagtypes(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            tagtypes = result.get("response", {}).get("settings", [])
            if not tagtypes:
                typer.echo("No TagTypes found.")
            else:
                typer.echo(format_list_markdown("TagTypes", tagtypes, [
                    ("ID", "id"), ("NAME", "name"), ("OWNER", "owner"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list TagTypes. {message} Status code: {status}", "TagType", "list"))
            raise typer.Exit(code=status)
