import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown

searchlist_app = typer.Typer()

# The fields the server requires on every create and update request.
_REQUIRED_FIELDS = ("url", "title", "role", "boost")


def _parse_fields(fields: Optional[List[str]]) -> dict:
    parsed = {}
    for item in fields or []:
        key, sep, value = item.partition("=")
        if not sep or not key:
            typer.echo(format_result_markdown(False, f"Invalid --field '{item}'. Use KEY=VALUE.", "Document", "field"))
            raise typer.Exit(code=1)
        parsed[key] = value
    return parsed


def _collect_changes(url, title, content, role, boost, label, fields) -> dict:
    changes = {
        key: value
        for key, value in (
            ("url", url),
            ("title", title),
            ("content", content),
            ("role", role or None),
            ("boost", boost),
            ("label", label or None),
        )
        if value is not None
    }
    changes.update(_parse_fields(fields))
    return changes


def _join(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return value


def _shorten(value) -> str:
    if isinstance(value, str) and len(value) > 200:
        return value[:200] + "..."
    return value


def _failed(message: str, status: int, action: str, what: str):
    typer.echo(format_result_markdown(False, f"Failed to {what}. {message} Status code: {status}", "Document", action))
    raise typer.Exit(code=status)


def _emit(result: dict, output: str) -> bool:
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
        return True
    if output == "yaml":
        typer.echo(yaml.dump(result))
        return True
    return False


@searchlist_app.command("search")
def search_documents(
    query: str = typer.Argument(
        None, help="Search query (default: all documents)"),
    start: int = typer.Option(
        None, "--start", help="0-based offset of the first hit"),
    size: int = typer.Option(
        None, "--size", "-s", help="Number of hits to return (the server caps it at 100)"),
    sort: str = typer.Option(
        None, "--sort", help="Sort expression, e.g. last_modified.desc"),
    lang: List[str] = typer.Option(
        None, "--lang", help="Restrict to a language (repeatable)"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Search the indexed documents (admin document browser).
    """
    client = FessAPIClient(Settings())
    result = client.search_documents(query=query, start=start, size=size, sort=sort, lang=lang or None)
    response = result.get("response", {})
    status = response.get("status", 1)

    if not _emit(result, output):
        if status == 0:
            docs = response.get("docs", [])
            if not docs:
                typer.echo("No documents found.")
            else:
                typer.echo(format_list_markdown(
                    f"Documents ({response.get('start_record_number')}-{response.get('end_record_number')}"
                    f" of {response.get('record_count')})",
                    docs,
                    [
                        ("DOC ID", "doc_id"),
                        ("TITLE", "title"),
                        ("URL", "url"),
                        ("LAST MODIFIED", "last_modified"),
                    ],
                ))
        else:
            _failed(response.get("message", ""), status, "search", "search documents")
    elif status != 0:
        raise typer.Exit(code=status)


@searchlist_app.command("get")
def get_document(
    doc_id: str = typer.Argument(..., help="Document doc_id"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Retrieve an indexed document by its doc_id.
    """
    client = FessAPIClient(Settings())
    result = client.get_document(doc_id)
    status = result.get("response", {}).get("status", 1)

    if not _emit(result, output):
        if status == 0:
            doc = result.get("response", {}).get("doc", {})
            typer.echo(format_detail_markdown(
                f"Document Details: {doc.get('title', '-')}",
                doc,
                [
                    ("doc_id", "doc_id"),
                    ("url", "url"),
                    ("title", "title"),
                    ("content", "content"),
                    ("role", "role"),
                    ("label", "label"),
                    ("lang", "lang"),
                    ("boost", "boost"),
                    ("mimetype", "mimetype"),
                    ("content_length", "content_length"),
                    ("click_count", "click_count"),
                    ("favorite_count", "favorite_count"),
                    ("last_modified", "last_modified"),
                    ("timestamp", "timestamp"),
                ],
                transforms={"content": _shorten, "role": _join, "label": _join, "lang": _join},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            _failed(message, status, "get", "retrieve document")
    elif status != 0:
        raise typer.Exit(code=status)


@searchlist_app.command("create")
def create_document(
    url: str = typer.Option(..., "--url", help="Document URL"),
    title: str = typer.Option(..., "--title", help="Document title"),
    role: List[str] = typer.Option(
        ..., "--role", help="Role allowed to see the document, e.g. Rguest (repeatable)"),
    content: str = typer.Option(None, "--content", help="Document content"),
    boost: float = typer.Option(1.0, "--boost", help="Boost value"),
    label: List[str] = typer.Option(
        None, "--label", help="Label value (repeatable)"),
    field: List[str] = typer.Option(
        None, "--field", help="Any other field as KEY=VALUE (repeatable), e.g. mimetype=text/plain"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Index a new document.
    """
    doc = _collect_changes(url, title, content, role, boost, label, field)
    client = FessAPIClient(Settings())
    result = client.create_document(doc)
    status = result.get("response", {}).get("status", 1)

    if not _emit(result, output):
        if status == 0:
            doc_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"Document '{doc_id}' created successfully.", "Document", "create", doc_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            _failed(message, status, "create", "create document")
    elif status != 0:
        raise typer.Exit(code=status)


@searchlist_app.command("update")
def update_document(
    doc_id: str = typer.Argument(..., help="Document doc_id"),
    url: str = typer.Option(None, "--url", help="New document URL"),
    title: str = typer.Option(None, "--title", help="New title"),
    content: str = typer.Option(None, "--content", help="New content"),
    role: List[str] = typer.Option(
        None, "--role", help="Replace the roles (repeatable)"),
    boost: float = typer.Option(None, "--boost", help="New boost value"),
    label: List[str] = typer.Option(
        None, "--label", help="Replace the labels (repeatable)"),
    field: List[str] = typer.Option(
        None, "--field", help="Any other field as KEY=VALUE (repeatable)"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Update an indexed document. Only the given fields change.
    """
    changes = _collect_changes(url, title, content, role, boost, label, field)
    if not changes:
        typer.echo(format_result_markdown(False, "Nothing to update. Give at least one field option.", "Document", "update", doc_id))
        raise typer.Exit(code=1)

    # The server validates the request body on its own: url, title, role and boost
    # must be present even when they do not change, so send the stored values back.
    client = FessAPIClient(Settings())
    current = client.get_document(doc_id)
    current_status = current.get("response", {}).get("status", 1)
    if current_status != 0:
        message: str = current.get("response", {}).get("message", "")
        _failed(message, current_status, "update", "retrieve document")
    stored = current.get("response", {}).get("doc", {})
    doc = {key: stored[key] for key in _REQUIRED_FIELDS if key in stored}
    doc["doc_id"] = doc_id
    doc.update(changes)

    result = client.update_document(doc)
    status = result.get("response", {}).get("status", 1)

    if not _emit(result, output):
        if status == 0:
            typer.echo(format_result_markdown(True, f"Document '{doc_id}' updated successfully.", "Document", "update", doc_id))
        else:
            message = result.get("response", {}).get("message", "")
            _failed(message, status, "update", "update document")
    elif status != 0:
        raise typer.Exit(code=status)


@searchlist_app.command("delete")
def delete_document(
    doc_id: str = typer.Argument(..., help="Document doc_id"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete an indexed document by its doc_id.
    """
    client = FessAPIClient(Settings())
    result = client.delete_document(doc_id)
    status = result.get("response", {}).get("status", 1)

    if not _emit(result, output):
        if status == 0:
            typer.echo(format_result_markdown(True, f"Document '{doc_id}' deleted successfully.", "Document", "delete", doc_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            _failed(message, status, "delete", "delete document")
    elif status != 0:
        raise typer.Exit(code=status)


@searchlist_app.command("delete-by-query")
def delete_documents_by_query(
    query: str = typer.Argument(..., help="Delete every document matching this query"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete every indexed document matching a query.
    """
    if not yes:
        typer.confirm(f"Delete all documents matching '{query}'?", abort=True)

    client = FessAPIClient(Settings())
    result = client.delete_documents_by_query(query)
    status = result.get("response", {}).get("status", 1)

    if not _emit(result, output):
        if status == 0:
            count = result.get("response", {}).get("count", 0)
            typer.echo(format_result_markdown(True, f"{count} document(s) deleted.", "Document", "delete-by-query"))
        else:
            message: str = result.get("response", {}).get("message", "")
            _failed(message, status, "delete-by-query", "delete documents")
    elif status != 0:
        raise typer.Exit(code=status)
