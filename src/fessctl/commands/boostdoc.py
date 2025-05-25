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

boostdoc_app = typer.Typer()


@boostdoc_app.command("create")
def create_boostdoc(
    url_expr: str = typer.Option(..., "--url-expr",
                                 help="Regular expression for URLs"),
    boost_expr: str = typer.Option(..., "--boost-expr",
                                   help="Boost value expression"),
    sort_order: int = typer.Option(..., "--sort-order",
                                   help="Sort order (non-negative integer)"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time", help="Created time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new BoostDoc.
    """
    client = FessAPIClient(Settings())(Settings())

    config = {
        "crud_mode": 1,
        "url_expr": url_expr,
        "boost_expr": boost_expr,
        "sort_order": sort_order,
        "created_by": created_by,
        "created_time": created_time,
    }

    result = client.create_boostdoc(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            boostdoc_id = result.get("response", {}).get("id", "")
            typer.secho(
                f"BoostDoc '{boostdoc_id}' created successfully.", fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to create BoostDoc. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@boostdoc_app.command("update")
def update_boostdoc(
    config_id: str = typer.Argument(..., help="BoostDoc ID"),
    url_expr: Optional[str] = typer.Option(
        None, "--url-expr", help="URL expression"),
    boost_expr: Optional[str] = typer.Option(
        None, "--boost-expr", help="Boost value expression"),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order (non-negative integer)"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Update an existing BoostDoc.
    """
    client = FessAPIClient(Settings())
    result = client.get_boostdoc(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"BoostDoc with ID '{config_id}' not found. {message}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if url_expr is not None:
        config["url_expr"] = url_expr
    if boost_expr is not None:
        config["boost_expr"] = boost_expr
    if sort_order is not None:
        config["sort_order"] = sort_order

    result = client.update_boostdoc(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"BoostDoc '{config_id}' updated successfully.", fg=typer.colors.GREEN)
        else:
            message = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to update BoostDoc. {message} Status code: {status}", fg=typer.colors.RED)
            raise typer.Exit(code=status)


@boostdoc_app.command("delete")
def delete_boostdoc(
    config_id: str = typer.Argument(..., help="BoostDoc ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a BoostDoc by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_boostdoc(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"BoostDoc '{config_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete BoostDoc. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@boostdoc_app.command("get")
def get_boostdoc(
    config_id: str = typer.Argument(..., help="BoostDoc ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a BoostDoc by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_boostdoc(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            boostdoc = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(title=f"BoostDoc Details: {boostdoc.get('id', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row("id", str(boostdoc.get("id", "-")))
            table.add_row("url_expr", str(boostdoc.get("url_expr", "-")))
            table.add_row("boost_expr", str(boostdoc.get("boost_expr", "-")))
            table.add_row("sort_order", str(boostdoc.get("sort_order", "-")))
            table.add_row("version_no", str(boostdoc.get("version_no", "-")))
            table.add_row("crud_mode", str(boostdoc.get("crud_mode", "-")))
            table.add_row("updated_by", str(boostdoc.get("updated_by", "-")))
            table.add_row("updated_time", to_utc_iso8601(
                boostdoc.get("updated_time")))
            table.add_row("created_by", str(boostdoc.get("created_by", "-")))
            table.add_row("created_time", to_utc_iso8601(
                boostdoc.get("created_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve BoostDoc. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@boostdoc_app.command("list")
def list_boostdocs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List BoostDocs.
    """
    client = FessAPIClient(Settings())
    result = client.list_boostdocs(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            boostdocs = result.get("response", {}).get("settings", [])
            if not boostdocs:
                typer.secho("No BoostDocs found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="BoostDocs")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("URL_EXPR", style="magenta")
                table.add_column("BOOST_EXPR", style="green")
                table.add_column("SORT_ORDER", style="yellow")
                table.add_column("UPDATED_BY", style="blue")
                table.add_column("UPDATED_TIME", style="white")

                for boostdoc in boostdocs:
                    table.add_row(
                        boostdoc.get("id", "-"),
                        boostdoc.get("url_expr", "-"),
                        boostdoc.get("boost_expr", "-"),
                        str(boostdoc.get("sort_order", "-")),
                        boostdoc.get("updated_by", "-"),
                        to_utc_iso8601(boostdoc.get("updated_time")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list BoostDocs. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
