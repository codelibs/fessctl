import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

failureurl_app = typer.Typer()


@failureurl_app.command("delete")
def delete_failureurl(
    failureurl_id: str = typer.Argument(..., help="FailureUrl ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete a FailureUrl by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_failureurl(failureurl_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"FailureUrl '{failureurl_id}' deleted successfully.", "FailureUrl", "delete", failureurl_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete FailureUrl. {message} Status code: {status}", "FailureUrl", "delete"))
            raise typer.Exit(code=status)


@failureurl_app.command("delete-all")
def delete_all_failureurls(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete all FailureUrls.
    """
    if not yes:
        typer.confirm("Delete all FailureUrls?", abort=True)

    client = FessAPIClient(Settings())
    result = client.delete_all_failureurls()
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, "All FailureUrls deleted successfully.", "FailureUrl", "delete-all"))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete all FailureUrls. {message} Status code: {status}", "FailureUrl", "delete-all"))
            raise typer.Exit(code=status)


@failureurl_app.command("get")
def get_failureurl(
    failureurl_id: str = typer.Argument(..., help="FailureUrl ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Retrieve a FailureUrl by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_failureurl(failureurl_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            failureurl = result.get("response", {}).get("log", {})
            typer.echo(format_detail_markdown(
                f"FailureUrl Details: {failureurl.get('url', '-')}",
                failureurl,
                [
                    ("id", "id"),
                    ("url", "url"),
                    ("error_name", "error_name"),
                    ("error_count", "error_count"),
                    ("last_access_time", "last_access_time"),
                    ("config_id", "config_id"),
                    ("thread_name", "thread_name"),
                    ("error_log", "error_log"),
                ],
                transforms={"last_access_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve FailureUrl. {message} Status code: {status}", "FailureUrl", "get"))
            raise typer.Exit(code=status)


@failureurl_app.command("list")
def list_failureurls(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    url: str = typer.Option(None, "--url", help="Filter by the URL that failed"),
    error_name: str = typer.Option(
        None, "--error-name", help="Filter by error name"),
    error_count_min: int = typer.Option(
        None, "--error-count-min", help="Minimum error count"),
    error_count_max: int = typer.Option(
        None, "--error-count-max", help="Maximum error count"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List FailureUrls (URLs that failed during crawling).
    """
    filters = {
        key: value
        for key, value in (
            ("url", url),
            ("error_name", error_name),
            ("error_count_min", error_count_min),
            ("error_count_max", error_count_max),
        )
        if value is not None
    }
    client = FessAPIClient(Settings())
    result = client.list_failureurls(page=page, size=size, filters=filters)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            failureurls = result.get("response", {}).get("logs", [])
            if not failureurls:
                typer.echo("No FailureUrls found.")
            else:
                display_items = []
                for item in failureurls:
                    d = dict(item)
                    d["last_access_time_display"] = to_utc_iso8601(item.get("last_access_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("FailureUrls", display_items, [
                    ("ID", "id"),
                    ("URL", "url"),
                    ("ERROR", "error_name"),
                    ("COUNT", "error_count"),
                    ("LAST ACCESS TIME", "last_access_time_display"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list FailureUrls. {message} Status code: {status}", "FailureUrl", "list"))
            raise typer.Exit(code=status)
