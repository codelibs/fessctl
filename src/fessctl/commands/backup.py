import json
from pathlib import Path

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown, output_error

backup_app = typer.Typer()


@backup_app.command("list")
def list_backup_files(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List the files that can be downloaded as a backup (index dumps, search logs, settings).
    """
    client = FessAPIClient(Settings())
    try:
        result = client.get_backup_files()
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            files = response.get("files", [])
            if not files:
                typer.echo("No Backup files found.")
            else:
                typer.echo(format_list_markdown("Backup files", files, [
                    ("NAME", "name"),
                    ("ID", "id"),
                ]))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list Backup files. {message} Status code: {status}", "Backup", "list"))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Backup", "list")
        raise typer.Exit(code=1)


@backup_app.command("download")
def download_backup_file(
    backup_id: str = typer.Argument(..., help="Backup file ID (the id shown by `backup list`)"),
    dest: Path = typer.Option(..., "--dest", "-d", help="File to write the backup file to"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite the destination file if it exists"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Download a backup file by ID.
    """
    client = FessAPIClient(Settings())
    try:
        if dest.exists() and not force:
            raise FileExistsError(f"'{dest}' already exists. Use --force to overwrite it.")

        result = client.download_backup_file(backup_id, dest)
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            typer.echo(format_result_markdown(True, f"Backup file '{backup_id}' downloaded to '{dest}' ({response.get('size')} bytes).", "Backup", "download", backup_id))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to download Backup file. {message} Status code: {status}", "Backup", "download"))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Backup", "download")
        raise typer.Exit(code=1)
