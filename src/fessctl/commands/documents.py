import json
from pathlib import Path

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown

documents_app = typer.Typer()


def _parse_documents(text: str) -> list:
    """
    Accepts a JSON array of documents, {"documents": [...]}, a single document
    object, or NDJSON (one document per line).
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(data, dict):
        data = data["documents"] if "documents" in data else [data]
    if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
        raise ValueError("expected a JSON array of document objects")
    return data


@documents_app.command("bulk")
def bulk_index(
    file: str = typer.Argument(
        ..., help="File with the documents (a JSON array, {\"documents\": [...]} or NDJSON), or - for stdin"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Index many documents in one request.

    Each document needs a url and a title; role, boost, the counters and the
    timestamps are filled in by the server when omitted.
    """
    try:
        text = typer.get_text_stream("stdin").read() if file == "-" else Path(file).read_text(encoding="utf-8")
        documents = _parse_documents(text)
    except (OSError, ValueError) as e:
        typer.echo(format_result_markdown(False, f"Cannot read documents from '{file}'. {e}", "Document", "bulk"))
        raise typer.Exit(code=1)

    client = FessAPIClient(Settings())
    result = client.bulk_index_documents(documents)
    response = result.get("response", {})
    status = response.get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    elif status == 0:
        typer.echo(format_result_markdown(True, f"{len(response.get('items', []))} document(s) indexed.", "Document", "bulk"))
    else:
        message: str = response.get("message", "")
        items = response.get("items", [])
        if items:
            typer.echo(format_list_markdown("Bulk results", [dict(item, index=i + 1) for i, item in enumerate(items)], [
                ("#", "index"),
                ("RESULT", "result"),
                ("ID", "id"),
                ("MESSAGE", "message"),
            ]))
        typer.echo(format_result_markdown(False, f"Failed to index documents. {message} Status code: {status}", "Document", "bulk"))
    if status != 0:
        raise typer.Exit(code=status)
