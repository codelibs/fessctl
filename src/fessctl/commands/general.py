import json
from typing import List

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_result_markdown

general_app = typer.Typer()

# The update request must carry these (@Required in the Fess EditForm); every other setting that
# is left out keeps its stored value.
REQUIRED_KEYS = (
    "day_for_cleanup",
    "crawling_thread_count",
    "failure_count_threshold",
    "csv_file_encoding",
)

# Settings that the server leaves out of the GET response while they are unset.
UNSET_OMITTED_KEYS = (
    "ldap_provider_url",
    "ldap_security_principal",
    "ldap_admin_security_principal",
    "ldap_admin_security_credentials",
    "ldap_base_dn",
    "ldap_account_filter",
)


@general_app.command("get")
def get_general(
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Show the General system settings.
    """
    client = FessAPIClient(Settings())
    result = client.get_general()
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            setting = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                "General Settings", setting, [(key, key) for key in setting]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to get General settings. {message} Status code: {status}", "General", "get"))

    if status != 0:
        raise typer.Exit(code=status)


@general_app.command("update")
def update_general(
    settings: List[str] = typer.Option(
        [], "--set", help="Setting to change as KEY=VALUE (repeatable). KEY is a name shown by `general get`"
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"
    ),
):
    """
    Change General system settings; every setting not given keeps its value.

    Secrets are returned masked by `general get`. A new value replaces the stored secret, but one
    made only of '*' or empty is ignored by the server, so a secret cannot be cleared here
    (spnego_preauth_password is the exception: empty removes it). For any other setting an empty
    value stores an empty string.
    """
    changes = {}
    for item in settings:
        key, separator, value = item.partition("=")
        if not separator or not key:
            raise typer.BadParameter(f"'{item}' is not KEY=VALUE", param_hint="--set")
        changes[key] = value
    if not changes:
        raise typer.BadParameter("give at least one KEY=VALUE", param_hint="--set")

    client = FessAPIClient(Settings())
    current = client.get_general()
    status = current.get("response", {}).get("status", 1)
    if status != 0:
        message: str = current.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"Failed to get General settings. {message} Status code: {status}", "General", "update"))
        raise typer.Exit(code=status)
    setting = current.get("response", {}).get("setting", {})

    known = set(setting) | set(UNSET_OMITTED_KEYS)
    unknown = [key for key in changes if key not in known]
    if unknown:
        raise typer.BadParameter(
            f"unknown setting(s) for this Fess version: {', '.join(unknown)} (see `general get`)", param_hint="--set")

    request = {key: setting[key] for key in REQUIRED_KEYS if key in setting}
    for key, value in changes.items():
        if isinstance(setting.get(key), int):
            try:
                request[key] = int(value)
            except ValueError:
                raise typer.BadParameter(f"{key} takes an integer, got '{value}'", param_hint="--set")
        else:
            request[key] = value

    result = client.update_general(request)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"General settings updated ({', '.join(changes)}).", "General", "update"))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to update General settings. {message} Status code: {status}", "General", "update"))

    if status != 0:
        raise typer.Exit(code=status)
