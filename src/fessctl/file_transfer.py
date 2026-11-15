import json
from pathlib import Path
from typing import Callable, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClientError
from fessctl.utils import format_result_markdown


def _emit(result: dict, output: str, ok_message: str, fail_message: str,
          resource_type: str, action: str) -> None:
    """Prints the outcome of a transfer; exits with the API status when it failed."""
    response = result.get("response", {})
    status = response.get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    elif status == 0:
        typer.echo(format_result_markdown(True, ok_message, resource_type, action))
    else:
        typer.echo(format_result_markdown(
            False, f"{fail_message} {response.get('message', '')} Status code: {status}",
            resource_type, action))
    if status != 0:
        raise typer.Exit(code=status)


def _refuse(output: str, resource_type: str, action: str, message: str) -> None:
    """Reports a problem found before any request is made, in the requested format, and exits 1."""
    result = {"response": {"status": 1, "message": message}}
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        typer.echo(format_result_markdown(False, message, resource_type, action))
    raise typer.Exit(code=1)


def upload_file(file: Path, yes: bool, output: str, resource_type: str, prompt: str,
                send: Callable[[str], dict]) -> None:
    """Asks for confirmation, then sends the local file with ``send(path)``."""
    if not file.is_file():
        _refuse(output, resource_type, "upload", f"File '{file}' not found.")
    if not yes:
        typer.confirm(prompt, abort=True)
    result = send(str(file))
    _emit(result, output,
          f"'{file}' was accepted; Fess imports it in the background, so the result is not shown yet.",
          f"Failed to upload {resource_type}.", resource_type, "upload")


def download_file(file: Optional[Path], force: bool, output: str, resource_type: str,
                  fetch: Callable[[], bytes]) -> None:
    """Writes the content of ``fetch()`` to standard output, or to ``file``."""
    if file is not None and file.exists() and not force:
        _refuse(output, resource_type, "download", f"File '{file}' already exists. Use --force to overwrite it.")
    try:
        content = fetch()
    except FessAPIClientError as e:
        _emit({"response": {"status": 1, "message": e.content}}, output, "",
              f"Failed to download {resource_type}.", resource_type, "download")
        return
    if file is None:
        typer.echo(content, nl=False)
        return
    file.write_bytes(content)
    _emit({"response": {"status": 0, "path": str(file), "size": len(content)}}, output,
          f"{resource_type} saved to '{file}' ({len(content)} bytes).", "", resource_type, "download")
