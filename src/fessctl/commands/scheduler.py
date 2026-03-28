import datetime
import json
from typing import Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

scheduler_app = typer.Typer()


@scheduler_app.command("create")
def create_scheduler(
    name: str = typer.Option(..., "--name", help="Scheduler name"),
    target: str = typer.Option(..., "--target", help="Scheduler target"),
    script_type: str = typer.Option(..., "--script-type", help="Script type"),
    sort_order: int = typer.Option(1, "--sort-order", help="Sort order"),
    cron_expression: str = typer.Option(
        "", "--cron-expression", help="Cron expression"),
    script_data: str = typer.Option("", "--script-data", help="Script data"),
    crawler: str = typer.Option("", "--crawler", help="Crawler settings"),
    job_logging: str = typer.Option(
        "", "--job-logging", help="Job logging settings"),
    available: bool = typer.Option(
        True, "--available", help="Availability (true/false)"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Create a new Scheduler.
    """
    client = FessAPIClient(Settings())

    config = {
        "crud_mode": 1,
        "name": name,
        "target": target,
        "script_type": script_type,
        "sort_order": sort_order,
        "cron_expression": cron_expression,
        "script_data": script_data,
        "crawler": crawler,
        "job_logging": job_logging,
        "available": available,
        "created_by": created_by,
        "created_time": created_time,
    }
    result = client.create_scheduler(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            scheduler_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"Scheduler '{scheduler_id}' created successfully.", "Scheduler", "create", scheduler_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Operation failed. {message} Status code: {status}", "Scheduler", "create"))
            raise typer.Exit(code=status)


@scheduler_app.command("update")
def update_scheduler(
    scheduler_id: str = typer.Argument(..., help="Scheduler ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Scheduler name"),
    target: Optional[str] = typer.Option(
        None, "--target", help="Scheduler target"),
    cron_expression: Optional[str] = typer.Option(
        None, "--cron-expression", help="Cron expression"),
    script_type: Optional[str] = typer.Option(
        None, "--script-type", help="Script type"),
    script_data: Optional[str] = typer.Option(
        None, "--script-data", help="Script data"),
    crawler: Optional[str] = typer.Option(
        None, "--crawler", help="Crawler settings"),
    job_logging: Optional[str] = typer.Option(
        None, "--job-logging", help="Job logging settings"),
    available: Optional[bool] = typer.Option(
        None, "--available", help="Availability (true/false)"),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Update an existing Scheduler.
    """
    client = FessAPIClient(Settings())
    result = client.get_scheduler(scheduler_id)

    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"Scheduler with ID '{scheduler_id}' not found. {message}", "Scheduler", "update"))
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if name is not None:
        config["name"] = name
    if target is not None:
        config["target"] = target
    if cron_expression is not None:
        config["cron_expression"] = cron_expression
    if script_type is not None:
        config["script_type"] = script_type
    if script_data is not None:
        config["script_data"] = script_data
    if crawler is not None:
        config["crawler"] = crawler
    if job_logging is not None:
        config["job_logging"] = job_logging
    if available is not None:
        config["available"] = available
    if sort_order is not None:
        config["sort_order"] = sort_order

    result = client.update_scheduler(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            scheduler_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"Scheduler '{scheduler_id}' updated successfully.", "Scheduler", "update", scheduler_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Operation failed. {message} Status code: {status}", "Scheduler", "update"))
            raise typer.Exit(code=status)


@scheduler_app.command("delete")
def delete_scheduler(
    scheduler_id: str = typer.Argument(..., help="Scheduler ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a Scheduler by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_scheduler(scheduler_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"Scheduler '{scheduler_id}' deleted successfully.", "Scheduler", "delete", scheduler_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete Scheduler. {message} Status code: {status}", "Scheduler", "delete"))
            raise typer.Exit(code=status)


@scheduler_app.command("get")
def get_scheduler(
    scheduler_id: str = typer.Argument(..., help="Scheduler ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Retrieve a Scheduler by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_scheduler(scheduler_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            scheduler = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"Scheduler Details: {scheduler.get('name', '-')}",
                scheduler,
                [
                    ("id", "id"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                    ("version_no", "version_no"),
                    ("crud_mode", "crud_mode"),
                    ("name", "name"),
                    ("target", "target"),
                    ("cron_expression", "cron_expression"),
                    ("script_type", "script_type"),
                    ("script_data", "script_data"),
                    ("crawler", "crawler"),
                    ("job_logging", "job_logging"),
                    ("available", "available"),
                    ("sort_order", "sort_order"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                ],
                transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve Scheduler. {message} Status code: {status}", "Scheduler", "get"))
            raise typer.Exit(code=status)


@scheduler_app.command("list")
def list_schedulers(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List Schedulers.
    """
    client = FessAPIClient(Settings())
    result = client.list_schedulers(page=page, size=size)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            schedulers = result.get("response", {}).get("settings", [])
            if not schedulers:
                typer.echo("No Schedulers found.")
            else:
                typer.echo(format_list_markdown("Schedulers", schedulers, [
                    ("ID", "id"), ("NAME", "name"), ("AVAILABLE", "available"),
                    ("TARGET", "target"), ("CRON", "cron_expression"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list Schedulers. {message} Status code: {status}", "Scheduler", "list"))
            raise typer.Exit(code=status)


@scheduler_app.command("start")
def start_scheduler(
    scheduler_id: str = typer.Argument(..., help="Scheduler ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Start a Scheduler by ID.
    """
    client = FessAPIClient(Settings())
    result = client.start_scheduler(scheduler_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            job_log_id = result.get("response", {}).get("jobLogId")
            message = f"Scheduler '{scheduler_id}' started successfully."
            if job_log_id:
                message += f" Job Log ID: {job_log_id}"
            typer.echo(format_result_markdown(True, message, "Scheduler", "start", scheduler_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to start Scheduler. {message} Status code: {status}", "Scheduler", "start"))
            raise typer.Exit(code=status)


@scheduler_app.command("stop")
def stop_scheduler(
    scheduler_id: str = typer.Argument(..., help="Scheduler ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Stop a Scheduler by ID.
    """
    client = FessAPIClient(Settings())
    result = client.stop_scheduler(scheduler_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"Scheduler '{scheduler_id}' stopped successfully.", "Scheduler", "stop", scheduler_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to stop Scheduler. {message} Status code: {status}", "Scheduler", "stop"))
            raise typer.Exit(code=status)
