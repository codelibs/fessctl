import json

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import to_utc_iso8601

crawlinginfo_app = typer.Typer()


@crawlinginfo_app.command("delete")
def delete_crawlinginfo(
    crawlinginfo_id: str = typer.Argument(..., help="CrawlingInfo ID"),
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
            typer.secho(
                f"CrawlingInfo '{crawlinginfo_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete CrawlingInfo. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@crawlinginfo_app.command("get")
def get_crawlinginfo(
    crawlinginfo_id: str = typer.Argument(..., help="CrawlingInfo ID"),
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
            console = Console()
            table = Table(
                title=f"CrawlingInfo Details: {crawlinginfo.get('job_name', '-')}"
            )
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # output all fields according to new schema
            table.add_row("id", str(crawlinginfo.get("id", "-")))
            table.add_row("session_id", str(
                crawlinginfo.get("session_id", "-")))
            table.add_row(
                "created_time", to_utc_iso8601(
                    crawlinginfo.get("created_time"))
            )
            # TODO add missing fields

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve CrawlingInfo. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
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
                typer.secho("No CrawlingInfos found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="CrawlingInfos")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("SESSION ID", style="cyan", no_wrap=True)
                table.add_column("CREATED TIME", style="cyan", no_wrap=True)
                for crawlinginfo in crawlinginfos:
                    table.add_row(
                        crawlinginfo.get("id", "-"),
                        crawlinginfo.get("session_id", "-"),
                        to_utc_iso8601(crawlinginfo.get("created_time")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list CrawlingInfos. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
