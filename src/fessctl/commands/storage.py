import json
from pathlib import Path
from typing import Optional

import click
import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown

storage_app = typer.Typer()

# Uploads and downloads move file content, so they get longer than the default request timeout.
TRANSFER_TIMEOUT = 300.0


def _object_path(item: dict) -> str:
    """The path to give the other storage commands: the item's directory plus its name."""
    directory = item.get("path")
    return f"{directory}/{item['name']}" if directory else item["name"]


def _echo_result(result: dict, output: str, success_message: str, failure_message: str, action: str, resource_id: str = ""):
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, success_message, "Storage", action, resource_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"{failure_message} {message} Status code: {status}", "Storage", action))

    if status != 0:
        raise typer.Exit(code=status)


@storage_app.command("list")
def list_storage(
    path: str = typer.Argument("", help="Directory to list, e.g. docs/2026 (default: the bucket root)"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List the objects and directories under a path of the configured object storage.
    """
    # Fess talks to the storage backend while serving this request; an unreachable
    # backend can take far longer than the default timeout to answer.
    client = FessAPIClient(Settings(), timeout=TRANSFER_TIMEOUT)
    result = client.get_storage_items(path)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            items = result.get("response", {}).get("items", [])
            if not items:
                typer.echo("No Storage items found.")
            else:
                rows = [{
                    "path": _object_path(item),
                    "type": "directory" if item.get("directory") else "file",
                    "size": item.get("size"),
                    "lastModified": item.get("lastModified"),
                } for item in items]
                typer.echo(format_list_markdown("Storage Items", rows, [
                    ("PATH", "path"),
                    ("TYPE", "type"),
                    ("SIZE", "size"),
                    ("LAST MODIFIED", "lastModified"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list Storage items. {message} Status code: {status}", "Storage", "list"))

    if status != 0:
        raise typer.Exit(code=status)


@storage_app.command("download")
def download_storage(
    path: str = typer.Argument(..., help="Object path, e.g. docs/report.pdf (see `storage list`)"),
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Write the object to this file (default: standard output)"
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite --file if it exists"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format for the result (text, json, yaml)"
    ),
):
    """
    Download an object to a file, or to standard output without --file.
    """
    if file is not None and file.exists() and not force:
        typer.echo(format_result_markdown(False, f"{file} already exists. Use --force to overwrite it.", "Storage", "download"))
        raise typer.Exit(code=1)

    if file is not None and not file.parent.is_dir():
        typer.echo(format_result_markdown(False, f"The directory {file.parent} does not exist.", "Storage", "download"))
        raise typer.Exit(code=1)

    client = FessAPIClient(Settings(), timeout=TRANSFER_TIMEOUT)
    response = client.download_storage_file(path)

    if response.headers.get("content-type", "").startswith("application/json"):
        # a failure that Fess could report before streaming
        result = response.json()
        status = result.get("response", {}).get("status", 1)
        _echo_result(result, output, "", "Failed to download Storage object.", "download")
        raise typer.Exit(code=status or 1)
    if response.headers.get("content-length") == "0":
        # Fess starts the response before it reads the object, so a missing object or an
        # unreachable storage comes back as a 200 with an explicit empty body (a real empty
        # object is sent chunked).
        result = {"response": {"status": 1, "message": "The server returned an empty response; check that the object exists and the storage is reachable."}}
        _echo_result(result, output, "", "Failed to download Storage object.", "download")
        raise typer.Exit(code=1)

    if file is None:
        click.get_binary_stream("stdout").write(response.content)
        return

    file.write_bytes(response.content)
    result = {"response": {"status": 0, "file": str(file), "size": len(response.content)}}
    _echo_result(result, output, f"Downloaded '{path}' to {file} ({len(response.content)} bytes).", "", "download", path)


@storage_app.command("upload")
def upload_storage(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="Local file to upload"),
    directory: str = typer.Option(
        "", "--dir", "-d", help="Directory in the storage to upload into, e.g. docs/2026 (default: the bucket root)"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Upload a file into a directory of the object storage under its own file name.
    An existing object of that name is overwritten. Not possible on Fess 15.6 to 15.8
    (the server cannot receive it); works on 14.x and 15.9+.
    """
    client = FessAPIClient(Settings(), timeout=TRANSFER_TIMEOUT)
    result = client.upload_storage_file(file, directory)
    target = f"{directory.strip('/')}/{file.name}" if directory.strip("/") else file.name
    _echo_result(result, output, f"Uploaded {file} as '{target}'.", "Failed to upload Storage object.", "upload", target)


@storage_app.command("delete")
def delete_storage(
    path: str = typer.Argument(..., help="Object path, e.g. docs/report.pdf (see `storage list`)"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete an object from the object storage.
    """
    if not yes:
        typer.confirm(f"Delete storage object '{path}'?", abort=True)

    client = FessAPIClient(Settings())
    result = client.delete_storage_file(path)
    _echo_result(result, output, f"Storage object '{path}' deleted successfully.", "Failed to delete Storage object.", "delete", path)
