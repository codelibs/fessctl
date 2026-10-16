import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_list_markdown, format_result_markdown

plugin_app = typer.Typer()


def _list_plugins(result: dict, title: str, action: str, output: str):
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            plugins = result.get("response", {}).get("plugins", [])
            if not plugins:
                typer.echo(f"No {title} found.")
            else:
                typer.echo(format_list_markdown(title, plugins, [
                    ("NAME", "name"),
                    ("VERSION", "version"),
                    ("TYPE", "type"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list {title}. {message} Status code: {status}", "Plugin", action))

    if status != 0:
        raise typer.Exit(code=status)


@plugin_app.command("installed")
def installed_plugins(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List the installed plugins.
    """
    client = FessAPIClient(Settings())
    _list_plugins(client.get_installed_plugins(), "Installed Plugins", "installed", output)


@plugin_app.command("available")
def available_plugins(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    List the plugins that can be installed from the configured plugin repositories.
    """
    client = FessAPIClient(Settings())
    _list_plugins(client.get_available_plugins(), "Available Plugins", "available", output)


@plugin_app.command("install")
def install_plugin(
    name: str = typer.Argument(..., help="Plugin name (see `plugin available`)"),
    version: str = typer.Argument(..., help="Plugin version"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Install a plugin by name and version. Fess downloads the jar in the background after the
    request is accepted, so check `plugin installed`; restart Fess to activate the plugin.
    """
    client = FessAPIClient(Settings())
    result = client.install_plugin(name, version)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"Installation of plugin '{name}' {version} requested; Fess downloads it in the background (see `plugin installed`). Restart Fess to activate it.", "Plugin", "install", name))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to install Plugin. {message} Status code: {status}", "Plugin", "install"))

    if status != 0:
        raise typer.Exit(code=status)


@plugin_app.command("uninstall")
def uninstall_plugin(
    name: str = typer.Argument(..., help="Plugin name (see `plugin installed`)"),
    version: str = typer.Argument(..., help="Installed plugin version"),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip the confirmation prompt"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Uninstall a plugin by name and version. Fess deletes the jar in the background after the
    request is accepted, and accepts it even when that plugin is not installed; check
    `plugin installed` and restart Fess for the removal to take effect.
    """
    if not yes:
        typer.confirm(f"Uninstall plugin '{name}' {version}?", abort=True)

    client = FessAPIClient(Settings())
    result = client.uninstall_plugin(name, version)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"Removal of plugin '{name}' {version} requested; Fess deletes it in the background (see `plugin installed`). Restart Fess for it to take effect.", "Plugin", "uninstall", name))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to uninstall Plugin. {message} Status code: {status}", "Plugin", "uninstall"))

    if status != 0:
        raise typer.Exit(code=status)
