import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_result_markdown, output_error

suggest_app = typer.Typer()


def delete_suggest_words(call, action: str, prompt: str, success: str, yes: bool, output: str):
    """
    Delete suggest words after confirmation; ``call`` runs the delete on the client.
    """
    if not yes:
        typer.confirm(prompt, abort=True)

    client = FessAPIClient(Settings())
    try:
        result = call(client)
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            typer.echo(format_result_markdown(True, success, "Suggest", action))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete the suggest words. {message} Status code: {status}", "Suggest", action))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Suggest", action)
        raise typer.Exit(code=1)


@suggest_app.command("info")
def suggest_info(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Show the number of words in the suggest index (all, from documents, from search queries).
    """
    client = FessAPIClient(Settings())
    try:
        result = client.get_suggest_info()
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            typer.echo(format_detail_markdown(
                "Suggest",
                response.get("setting", {}),
                [
                    ("total_words_num", "total_words_num"),
                    ("document_words_num", "document_words_num"),
                    ("query_words_num", "query_words_num"),
                ],
            ))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve the suggest info. {message} Status code: {status}", "Suggest", "info"))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Suggest", "info")
        raise typer.Exit(code=1)


@suggest_app.command("delete-all")
def delete_all_suggest_words(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete every word from the suggest index. Elevate words are restored by Fess afterwards;
    the other words come back the next time the suggest job runs.
    """
    delete_suggest_words(
        lambda c: c.delete_all_suggest_words(), "delete-all", "Delete all suggest words?",
        "All suggest words deleted successfully.", yes, output)


@suggest_app.command("delete-document")
def delete_document_suggest_words(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete the suggest words that come from documents.
    """
    delete_suggest_words(
        lambda c: c.delete_document_suggest_words(), "delete-document", "Delete the suggest words from documents?",
        "Suggest words from documents deleted successfully.", yes, output)


@suggest_app.command("delete-query")
def delete_query_suggest_words(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Delete the suggest words that come from search queries.
    """
    delete_suggest_words(
        lambda c: c.delete_query_suggest_words(), "delete-query", "Delete the suggest words from search queries?",
        "Suggest words from search queries deleted successfully.", yes, output)
