import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown, output_error

stats_app = typer.Typer()


def flatten(value, prefix: str = "") -> list[dict]:
    """
    Flatten nested stats into NAME/VALUE rows such as ``jvm.memory.heap.used``.
    List items are named by their ``key`` or ``path`` (``jvm.gc[young].count``), else by position.
    """
    if isinstance(value, dict):
        return [row for k, v in value.items() for row in flatten(v, f"{prefix}.{k}" if prefix else k)]
    if isinstance(value, list):
        rows = []
        for i, item in enumerate(value):
            if isinstance(item, dict):
                id_field = next((f for f in ("key", "path") if item.get(f)), None)
                if id_field:
                    rest = {k: v for k, v in item.items() if k != id_field}
                    rows.extend(flatten(rest, f"{prefix}[{item[id_field]}]"))
                    continue
            rows.extend(flatten(item, f"{prefix}[{i}]"))
        return rows
    return [{"name": prefix, "value": value}]


@stats_app.callback(invoke_without_command=True)
def show_stats(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Show the statistics of the Fess server: JVM, OS, process, search engine and filesystem.
    """
    client = FessAPIClient(Settings())
    try:
        result = client.get_stats()
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            typer.echo(format_list_markdown("Stats", flatten(response.get("stats", {})), [
                ("NAME", "name"),
                ("VALUE", "value"),
            ]))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve the stats. {message} Status code: {status}", "Stats", "show"))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "Stats", "show")
        raise typer.Exit(code=1)
