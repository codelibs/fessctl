import datetime
import json
from typing import Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

relatedcontent_app = typer.Typer()


@relatedcontent_app.command("create")
def create_relatedcontent(
    term: str = typer.Option(..., "--term", help="Search term"),
    content: str = typer.Option(..., "--content", help="Related content"),
    sort_order: int = typer.Option(0, "--sort-order", help="Sort order"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time", help="Created time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new RelatedContent.
    """
    client = FessAPIClient(Settings())
    config = {
        "crud_mode": 1,
        "term": term,
        "content": content,
        "sort_order": sort_order,
        "created_by": created_by,
        "created_time": created_time,
    }

    if virtual_host:
        config["virtual_host"] = virtual_host

    result = client.create_relatedcontent(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, "RelatedContent created successfully.", "RelatedContent", "create"))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create RelatedContent. {message} Status code: {status}", "RelatedContent", "create"))
            raise typer.Exit(code=status)


@relatedcontent_app.command("update")
def update_relatedcontent(
    config_id: str = typer.Argument(..., help="RelatedContent ID"),
    term: Optional[str] = typer.Option(None, "--term", help="Search term"),
    content: Optional[str] = typer.Option(
        None, "--content", help="Related content"),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time", help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Update an existing RelatedContent.
    """
    client = FessAPIClient(Settings())
    result = client.get_relatedcontent(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"RelatedContent with ID '{config_id}' not found. {message}", "RelatedContent", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["id"] = config_id
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if term is not None:
        config["term"] = term
    if content is not None:
        config["content"] = content
    if sort_order is not None:
        config["sort_order"] = sort_order
    if virtual_host is not None:
        config["virtual_host"] = virtual_host

    result = client.update_relatedcontent(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"RelatedContent '{config_id}' updated successfully.", "RelatedContent", "update", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update RelatedContent. {message} Status code: {status}", "RelatedContent", "update"))
            raise typer.Exit(code=status)


@relatedcontent_app.command("delete")
def delete_relatedcontent(
    config_id: str = typer.Argument(..., help="RelatedContent ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a RelatedContent by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_relatedcontent(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"RelatedContent '{config_id}' deleted successfully.", "RelatedContent", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete RelatedContent. {message} Status code: {status}", "RelatedContent", "delete"))
            raise typer.Exit(code=status)


@relatedcontent_app.command("get")
def get_relatedcontent(
    config_id: str = typer.Argument(..., help="RelatedContent ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a RelatedContent by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_relatedcontent(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            relatedcontent = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"RelatedContent Details: {relatedcontent.get('id', '-')}",
                relatedcontent,
                [
                    ("id", "id"),
                    ("term", "term"),
                    ("content", "content"),
                    ("sort_order", "sort_order"),
                    ("virtual_host", "virtual_host"),
                    ("version_no", "version_no"),
                    ("crud_mode", "crud_mode"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                ],
                transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve RelatedContent. {message} Status code: {status}", "RelatedContent", "get"))
            raise typer.Exit(code=status)


@relatedcontent_app.command("list")
def list_relatedcontents(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List RelatedContents.
    """
    client = FessAPIClient(Settings())
    result = client.list_relatedcontents(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            relatedcontents = result.get("response", {}).get("settings", [])
            if not relatedcontents:
                typer.echo("No RelatedContents found.")
            else:
                typer.echo(format_list_markdown("RelatedContents", relatedcontents, [
                    ("ID", "id"),
                    ("TERM", "term"),
                    ("CONTENT", "content"),
                    ("VIRTUAL HOST", "virtual_host"),
                    ("SORT ORDER", "sort_order"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list RelatedContents. {message} Status code: {status}", "RelatedContent", "list"))
            raise typer.Exit(code=status)
