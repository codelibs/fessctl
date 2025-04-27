import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.commands.group import group_app
from fessctl.commands.role import role_app
from fessctl.commands.user import user_app
from fessctl.commands.webconfig import webconfig_app


app = typer.Typer(no_args_is_help=True)
app.add_typer(group_app, name="group")
app.add_typer(role_app, name="role")
app.add_typer(user_app, name="user")
app.add_typer(webconfig_app, name="webconfig")


@app.command()
def ping(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format: text, json, yaml"
    )
):
    """
    Check the health status of the Fess server.
    """
    client = FessAPIClient()
    try:
        result = client.ping()
        status = result.get("data", {}).get("status", "unknown")
        timed_out = result.get("data", {}).get("timed_out", True)

        if output == "json":
            typer.echo(json.dumps(result, indent=2))
        elif output == "yaml":
            typer.echo(yaml.dump(result))
        else:
            if status == "green" and not timed_out:
                typer.secho(
                    "Fess server is healthy (status: green).", fg=typer.colors.GREEN
                )
            elif status == "yellow":
                typer.secho(
                    f"Fess server status: {status} (timed_out: {timed_out})",
                    fg=typer.colors.YELLOW,
                )
            else:
                message: str = result.get("response", {}).get("message", "")
                typer.secho(
                    f"Fess server status: {status} (timed_out: {timed_out}) {message}",
                    fg=typer.colors.RED,
                )
                raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
