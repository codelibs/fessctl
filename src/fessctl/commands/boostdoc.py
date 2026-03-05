import datetime
import json
from typing import Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

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
    client = FessAPIClient(Settings())

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
            typer.echo(format_result_markdown(True, f"BoostDoc '{boostdoc_id}' created successfully.", "BoostDoc", "create", boostdoc_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create BoostDoc. {message} Status code: {status}", "BoostDoc", "create"))
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
        typer.echo(format_result_markdown(False, f"BoostDoc with ID '{config_id}' not found. {message}", "BoostDoc", "update"))
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
            typer.echo(format_result_markdown(True, f"BoostDoc '{config_id}' updated successfully.", "BoostDoc", "update", config_id))
        else:
            message = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update BoostDoc. {message} Status code: {status}", "BoostDoc", "update"))
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
            typer.echo(format_result_markdown(True, f"BoostDoc '{config_id}' deleted successfully.", "BoostDoc", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete BoostDoc. {message} Status code: {status}", "BoostDoc", "delete"))
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
            typer.echo(format_detail_markdown(
                f"BoostDoc Details: {boostdoc.get('id', '-')}",
                boostdoc,
                [
                    ("id", "id"),
                    ("url_expr", "url_expr"),
                    ("boost_expr", "boost_expr"),
                    ("sort_order", "sort_order"),
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
            typer.echo(format_result_markdown(False, f"Failed to retrieve BoostDoc. {message} Status code: {status}", "BoostDoc", "get"))
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
                typer.echo("No BoostDocs found.")
            else:
                display_items = []
                for item in boostdocs:
                    d = dict(item)
                    d["updated_time_display"] = to_utc_iso8601(item.get("updated_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("BoostDocs", display_items, [
                    ("ID", "id"), ("URL_EXPR", "url_expr"), ("BOOST_EXPR", "boost_expr"),
                    ("SORT_ORDER", "sort_order"), ("UPDATED_BY", "updated_by"),
                    ("UPDATED_TIME", "updated_time_display"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list BoostDocs. {message} Status code: {status}", "BoostDoc", "list"))
            raise typer.Exit(code=status)
