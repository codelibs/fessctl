import datetime
import json
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import to_utc_iso8601

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
            typer.secho("RelatedContent created successfully.",
                        fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(f"Failed to create RelatedContent. {message} Status code: {status}",
                        fg=typer.colors.RED)
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
        typer.secho(
            f"RelatedContent with ID '{config_id}' not found. {message}", fg=typer.colors.RED)
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
            typer.secho(
                f"RelatedContent '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update RelatedContent. {message} Status code: {status}", fg=typer.colors.RED)
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
            typer.secho(
                f"RelatedContent '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete RelatedContent. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
            console = Console()
            table = Table(
                title=f"RelatedContent Details: {relatedcontent.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Output only valid fields for RelatedContent
            table.add_row("id", str(relatedcontent.get("id", "-")))
            table.add_row("term", str(relatedcontent.get("term", "-")))
            table.add_row("content", str(relatedcontent.get("content", "-")))
            table.add_row("sort_order", str(
                relatedcontent.get("sort_order", "-")))
            table.add_row("virtual_host", str(
                relatedcontent.get("virtual_host", "-")))
            table.add_row("version_no", str(
                relatedcontent.get("version_no", "-")))
            table.add_row("crud_mode", str(
                relatedcontent.get("crud_mode", "-")))
            table.add_row("updated_by", str(
                relatedcontent.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                relatedcontent.get("updated_time")))
            table.add_row("created_by", str(
                relatedcontent.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                relatedcontent.get("created_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve RelatedContent. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
                typer.secho("No RelatedContents found.",
                            fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="RelatedContents")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("TERM", style="magenta")
                table.add_column("CONTENT", style="magenta")
                table.add_column("VIRTUAL HOST", style="green")
                table.add_column("SORT ORDER", style="yellow")

                for rc in relatedcontents:
                    table.add_row(
                        rc.get("id", "-"),
                        rc.get("term", "-"),
                        rc.get("content", "-"),
                        rc.get("virtual_host", "-"),
                        str(rc.get("sort_order", "-")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list RelatedContents. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)
