import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

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
            typer.echo(format_result_markdown(True, f"JobLog '{joblog_id}' deleted successfully.", "JobLog", "delete", joblog_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete JobLog. {message} Status code: {status}", "JobLog", "delete"))
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
            typer.echo(format_detail_markdown(
                f"JobLog Details: {joblog.get('job_name', '-')}",
                joblog,
                [
                    ("id", "id"),
                    ("job_name", "job_name"),
                    ("job_status", "job_status"),
                    ("target", "target"),
                    ("script_type", "script_type"),
                    ("script_data", "script_data"),
                    ("script_result", "script_result"),
                    ("start_time", "start_time"),
                    ("end_time", "end_time"),
                ],
                transforms={"start_time": to_utc_iso8601, "end_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve JobLog. {message} Status code: {status}", "JobLog", "get"))
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
                typer.echo("No JobLogs found.")
            else:
                display_items = []
                for item in joblogs:
                    d = dict(item)
                    d["start_time_display"] = to_utc_iso8601(item.get("start_time"))
                    d["end_time_display"] = to_utc_iso8601(item.get("end_time"))
                    display_items.append(d)
                typer.echo(format_list_markdown("JobLogs", display_items, [
                    ("ID", "id"),
                    ("NAME", "job_name"),
                    ("STATUS", "job_status"),
                    ("START TIME", "start_time_display"),
                    ("END TIME", "end_time_display"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list JobLogs. {message} Status code: {status}", "JobLog", "list"))
            raise typer.Exit(code=status)
