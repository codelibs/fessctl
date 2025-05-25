import json

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import to_utc_iso8601

joblog_app = typer.Typer()


@joblog_app.command("delete")
def delete_joblog(
    joblog_id: str = typer.Argument(..., help="JobLog ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a JobLog by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_joblog(joblog_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.secho(
                f"JobLog '{joblog_id}' deleted successfully.",
                fg=typer.colors.GREEN,
            )
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to delete JobLog. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@joblog_app.command("get")
def get_joblog(
    joblog_id: str = typer.Argument(..., help="JobLog ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Retrieve a JobLog by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_joblog(joblog_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            joblog = result.get("response", {}).get("log", {})
            console = Console()
            table = Table(
                title=f"JobLog Details: {joblog.get('job_name', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # output all fields according to new schema
            table.add_row("id", str(joblog.get("id", "-")))
            table.add_row("job_name", str(joblog.get("job_name", "-")))
            table.add_row("job_status", str(joblog.get("job_status", "-")))
            table.add_row("target", str(joblog.get("target", "-")))
            table.add_row("script_type", str(joblog.get("script_type", "-")))
            table.add_row("script_data", str(joblog.get("script_data", "-")))
            table.add_row("script_result", str(
                joblog.get("script_result", "-")))
            table.add_row("start_time", to_utc_iso8601(
                joblog.get("start_time")))
            table.add_row("end_time", to_utc_iso8601(joblog.get("end_time")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve JobLog. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@joblog_app.command("list")
def list_joblogs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List JobLogs.
    """
    client = FessAPIClient(Settings())
    result = client.list_joblogs(page=page, size=size)
    status = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            joblogs = result.get("response", {}).get("logs", [])
            if not joblogs:
                typer.secho("No JobLogs found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="JobLogs")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("NAME", style="cyan", no_wrap=True)
                table.add_column("STATUS", style="cyan", no_wrap=True)
                table.add_column("START TIME", style="cyan", no_wrap=True)
                table.add_column("END TIME", style="cyan", no_wrap=True)
                for joblog in joblogs:
                    table.add_row(
                        joblog.get("id", "-"),
                        joblog.get("job_name", "-"),
                        joblog.get("job_status", "-"),
                        to_utc_iso8601(joblog.get("start_time")),
                        to_utc_iso8601(joblog.get("end_time")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list JobLogs. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
