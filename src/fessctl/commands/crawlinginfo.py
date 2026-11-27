import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, id_help, to_utc_iso8601

crawlinginfo_app = typer.Typer()


@crawlinginfo_app.command("delete")
def delete_crawlinginfo(
    crawlinginfo_id: str = typer.Argument(..., help=id_help("CrawlingInfo ID")),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete a CrawlingInfo by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_crawlinginfo(crawlinginfo_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"CrawlingInfo '{crawlinginfo_id}' deleted successfully.", "CrawlingInfo", "delete", crawlinginfo_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete CrawlingInfo. {message} Status code: {status}", "CrawlingInfo", "delete"))
    if status != 0:
        raise typer.Exit(code=status)


@crawlinginfo_app.command("delete-all")
def delete_all_crawlinginfos(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete all CrawlingInfo sessions except the running ones.
    """
    if not yes:
        typer.confirm("Delete all CrawlingInfo sessions except the running ones?", abort=True)

    client = FessAPIClient(Settings())
    result = client.delete_all_crawlinginfos()
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, "All CrawlingInfo sessions except the running ones deleted successfully.", "CrawlingInfo", "delete-all"))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete all CrawlingInfos. {message} Status code: {status}", "CrawlingInfo", "delete-all"))
    if status != 0:
        raise typer.Exit(code=status)


@crawlinginfo_app.command("get")
def get_crawlinginfo(
    crawlinginfo_id: str = typer.Argument(..., help=id_help("CrawlingInfo ID")),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Retrieve a CrawlingInfo by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_crawlinginfo(crawlinginfo_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            crawlinginfo = result.get("response", {}).get("log", {})
            typer.echo(format_detail_markdown(
                f"CrawlingInfo Details: {crawlinginfo.get('job_name', '-')}",
                crawlinginfo,
                [
                    ("id", "id"),
                    ("session_id", "session_id"),
                    ("created_time", "created_time"),
                ],
                transforms={"created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve CrawlingInfo. {message} Status code: {status}", "CrawlingInfo", "get"))
    if status != 0:
        raise typer.Exit(code=status)


@crawlinginfo_app.command("list")
def list_crawlinginfos(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List CrawlingInfos.
    """
    client = FessAPIClient(Settings())
    result = client.list_crawlinginfos(page=page, size=size)
    status = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            crawlinginfos = result.get("response", {}).get("logs", [])
            if not crawlinginfos:
                typer.echo("No CrawlingInfos found.")
            else:
                display_items = []
                for item in crawlinginfos:
                    d = dict(item)
                    d["created_time_display"] = to_utc_iso8601(item.get("created_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("CrawlingInfos", display_items, [
                    ("ID", "id"),
                    ("SESSION ID", "session_id"),
                    ("CREATED TIME", "created_time_display"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list CrawlingInfos. {message} Status code: {status}", "CrawlingInfo", "list"))
    if status != 0:
        raise typer.Exit(code=status)


@crawlinginfo_app.command("progress")
def progress_crawlinginfo(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Show the progress of the running crawls (Fess 15.10 and later).
    """
    client = FessAPIClient(Settings())
    result = client.get_crawlinginfo_progress()
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            running = result.get("response", {}).get("progress", [])
            if not running:
                typer.echo("No running crawls found.")
            else:
                display_items = []
                for item in running:
                    d = dict(item)
                    # percent is left out when there is no previous completed crawl to compare with
                    d["percent_display"] = f"{item['percent']}%" if item.get("percent") is not None else None
                    d["updated_time_display"] = to_utc_iso8601(item.get("updated_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("Running crawls", display_items, [
                    ("NAME", "name"),
                    ("CONFIG ID", "config_id"),
                    ("COUNT", "count"),
                    ("LAST COUNT", "last_count"),
                    ("PERCENT", "percent_display"),
                    ("UPDATED TIME", "updated_time_display"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve the progress of crawls. {message} Status code: {status}", "CrawlingInfo", "progress"))
    if status != 0:
        raise typer.Exit(code=status)
