import json

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.commands.accesstoken import accesstoken_app
# from fessctl.commands.backup import backup_app
from fessctl.commands.badword import badword_app
from fessctl.commands.boostdoc import boostdoc_app
from fessctl.commands.crawlinginfo import crawlinginfo_app
from fessctl.commands.dataconfig import dataconfig_app
from fessctl.commands.duplicatehost import duplicatehost_app
from fessctl.commands.elevateword import elevateword_app
from fessctl.commands.fileauth import fileauth_app
from fessctl.commands.fileconfig import fileconfig_app
from fessctl.commands.group import group_app
from fessctl.commands.joblog import joblog_app
from fessctl.commands.keymatch import keymatch_app
from fessctl.commands.labeltype import labeltype_app
from fessctl.commands.role import role_app
from fessctl.commands.scheduler import scheduler_app
from fessctl.commands.user import user_app
from fessctl.commands.webauth import webauth_app
from fessctl.commands.webconfig import webconfig_app


app = typer.Typer(no_args_is_help=True)
app.add_typer(accesstoken_app, name="accesstoken")
# app.add_typer(backup_app, name="backup")
app.add_typer(badword_app, name="badword")
app.add_typer(boostdoc_app, name="boostdoc")
app.add_typer(crawlinginfo_app, name="crawlinginfo")
app.add_typer(dataconfig_app, name="dataconfig")
app.add_typer(duplicatehost_app, name="duplicatehost")
app.add_typer(elevateword_app, name="elevateword")
app.add_typer(fileauth_app, name="fileauth")
app.add_typer(fileconfig_app, name="fileconfig")
app.add_typer(group_app, name="group")
app.add_typer(joblog_app, name="joblog")
app.add_typer(keymatch_app, name="keymatch")
app.add_typer(labeltype_app, name="labeltype")
app.add_typer(role_app, name="role")
app.add_typer(scheduler_app, name="scheduler")
app.add_typer(user_app, name="user")
app.add_typer(webauth_app, name="webauth")
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
