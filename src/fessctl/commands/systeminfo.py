import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown, output_error

systeminfo_app = typer.Typer()

# (title, key in the response) of the property groups, in display order
SECTIONS = [
    ("Bug Report", "bug_report_props"),
    ("Environment", "env_props"),
    ("Fess", "fess_props"),
    ("System", "system_props"),
]


@systeminfo_app.callback(invoke_without_command=True)
def show_systeminfo(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Show the system information of the Fess server: the bug report, environment,
    Fess and system properties.
    """
    client = FessAPIClient(Settings())
    try:
        result = client.get_systeminfo()
        response = result.get("response", {})
        status = response.get("status", 1)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        elif status == 0:
            typer.echo("\n\n".join(
                format_list_markdown(title, response.get(key, []), [
                    ("NAME", "label"),
                    ("VALUE", "value"),
                ])
                for title, key in SECTIONS
            ))
        else:
            message: str = response.get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve the system information. {message} Status code: {status}", "SystemInfo", "show"))
        if status != 0:
            raise typer.Exit(code=status)
    except typer.Exit:
        raise
    except Exception as e:
        output_error(output, e, "SystemInfo", "show")
        raise typer.Exit(code=1)
