import json
from pathlib import Path

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown, output_error

log_app = typer.Typer()


@log_app.command("list")
def list_log_files(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List the log files in the log directory of the Fess server.
    """
    client = FessAPIClient(Settings())
    try:
        result = client.get_log_files()
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            files = response.get("files", [])
            if not files:
                typer.echo("No Log files found.")
            else:
                typer.echo(format_list_markdown("Log files", files, [
                    ("NAME", "name"),
                    ("ID", "id"),
                    ("LAST MODIFIED", "lastModified"),
                ]))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list Log files. {message} Status code: {status}", "Log", "list"))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Log", "list")
        raise typer.Exit(code=1)


@log_app.command("download")
def download_log_file(
    log_id: str = typer.Argument(..., help="Log file ID (the id shown by `log list`)"),
    dest: Path = typer.Option(..., "--dest", "-d", help="File to write the log file to"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite the destination file if it exists"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Download a log file by ID.
    """
    client = FessAPIClient(Settings())
    try:
        if dest.exists() and not force:
            raise FileExistsError(f"'{dest}' already exists. Use --force to overwrite it.")

        # Fess answers an id that names no log file with an empty download, which cannot be
        # told from an empty log file, so check the id against the list first.
        result = client.get_log_files()
        if result.get("response", {}).get("status", 1) == 0:
            ids = [f.get("id") for f in result["response"].get("files", [])]
            if log_id in ids:
                result = client.download_log_file(log_id, dest)
            else:
                result = {"response": {"status": 1, "message": f"Log file '{log_id}' not found. See `log list` for the IDs."}}
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            typer.echo(format_result_markdown(True, f"Log file '{log_id}' downloaded to '{dest}' ({response.get('size')} bytes).", "Log", "download", log_id))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to download Log file. {message} Status code: {status}", "Log", "download"))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Log", "download")
        raise typer.Exit(code=1)
