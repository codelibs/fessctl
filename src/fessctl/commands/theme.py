import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown

theme_app = typer.Typer()


@theme_app.command("available")
def available_themes(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List the themes that can be installed (requires Fess 15.9+).
    """
    client = FessAPIClient(Settings())
    result = client.get_available_themes()
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            themes = result.get("response", {}).get("themes", [])
            if not themes:
                typer.echo("No Themes found.")
            else:
                typer.echo(format_list_markdown("Themes", themes, [
                    ("NAME", "name"),
                    ("VERSION", "version"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list Themes. {message} Status code: {status}", "Theme", "available"))
            raise typer.Exit(code=status)


@theme_app.command("install")
def install_theme(
    name: str = typer.Argument(..., help="Theme name (see `theme available`)"),
    version: str = typer.Argument(..., help="Theme version"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Install a theme by name and version (requires Fess 15.9+).
    """
    client = FessAPIClient(Settings())
    result = client.install_theme(name, version)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"Theme '{name}' {version} installed successfully.", "Theme", "install", name))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to install Theme. {message} Status code: {status}", "Theme", "install"))
            raise typer.Exit(code=status)
