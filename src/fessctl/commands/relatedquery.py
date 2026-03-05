import datetime
import json
from typing import Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

relatedquery_app = typer.Typer()


@relatedquery_app.command("create")
def create_relatedquery(
    term: str = typer.Option(..., "--term", help="Search term"),
    queries: str = typer.Option(..., "--queries", help="Query expressions"),
    version_no: int = typer.Option(..., "--version-no", help="Version number"),
    virtual_host: Optional[str] = typer.Option(
        None, "--virtual-host", help="Virtual host"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Create a new RelatedQuery.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "term": term,
        "queries": queries,
        "version_no": version_no,
        "created_by": created_by,
        "created_time": created_time,
    }

    if virtual_host:
        config["virtual_host"] = virtual_host

    result = client.create_relatedquery(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            relatedquery_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"RelatedQuery '{relatedquery_id}' created successfully.", "RelatedQuery", "create", relatedquery_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to create RelatedQuery. {message} Status code: {status}", "RelatedQuery", "create"))
            raise typer.Exit(code=status)


@relatedquery_app.command("update")
def update_relatedquery(
    config_id: str = typer.Argument(..., help="RelatedQuery ID"),
    term: Optional[str] = typer.Option(None, "--term", help="Search term"),
    queries: Optional[str] = typer.Option(
        None, "--queries", help="Query expressions"),
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
    Update an existing RelatedQuery.
    """
    client = FessAPIClient(Settings())
    result = client.get_relatedquery(config_id)

    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"RelatedQuery with ID '{config_id}' not found. {message}", "RelatedQuery", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["id"] = config_id
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if term is not None:
        config["term"] = term
    if queries is not None:
        config["queries"] = queries
    if virtual_host is not None:
        config["virtual_host"] = virtual_host

    result = client.update_relatedquery(config)
    status: int = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"RelatedQuery '{config_id}' updated successfully.", "RelatedQuery", "update", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update RelatedQuery. {message} Status code: {status}", "RelatedQuery", "update"))
            raise typer.Exit(code=status)


@relatedquery_app.command("delete")
def delete_relatedquery(
    config_id: str = typer.Argument(..., help="RelatedQuery ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a RelatedQuery by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_relatedquery(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"RelatedQuery '{config_id}' deleted successfully.", "RelatedQuery", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete RelatedQuery. {message} Status code: {status}", "RelatedQuery", "delete"))
            raise typer.Exit(code=status)


@relatedquery_app.command("get")
def get_relatedquery(
    config_id: str = typer.Argument(..., help="RelatedQuery ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"),
):
    """
    Retrieve a RelatedQuery by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_relatedquery(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            relatedquery = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"RelatedQuery Details: {relatedquery.get('id', '-')}",
                relatedquery,
                [
                    ("id", "id"),
                    ("term", "term"),
                    ("queries", "queries"),
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
            typer.echo(format_result_markdown(False, f"Failed to retrieve RelatedQuery. {message} Status code: {status}", "RelatedQuery", "get"))
            raise typer.Exit(code=status)


@relatedquery_app.command("list")
def list_relatedqueries(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List RelatedQueries.
    """
    client = FessAPIClient(Settings())
    result = client.list_relatedqueries(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            relatedqueries = result.get("response", {}).get("settings", [])
            if len(relatedqueries) == 0:
                typer.echo("No RelatedQueries found.")
            else:
                typer.echo(format_list_markdown("RelatedQueries", relatedqueries, [
                    ("ID", "id"),
                    ("TERM", "term"),
                    ("QUERIES", "queries"),
                    ("VIRTUAL HOST", "virtual_host"),
                    ("VERSION", "version_no"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list RelatedQueries. {message} Status code: {status}", "RelatedQuery", "list"))
            raise typer.Exit(code=status)
