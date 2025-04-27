import datetime
import json
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from fessctl.api.client import FessAPIClient

webconfig_app = typer.Typer()
client = FessAPIClient()

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; Fess/FessCTL; +http://fess.codelibs.org/bot.html)"
)


@webconfig_app.command("create")
def create_webconfig(
    name: str = typer.Option(..., "--name", help="WebConfig name"),
    urls: List[str] = typer.Option(..., "--url", help="Crawling target URLs"),
    user_agent: str = typer.Option(
        "Mozilla/5.0 (compatible; Fess/FessCTL; +http://fess.codelibs.org/bot.html)",
        "--user-agent",
        help="User agent string",
    ),
    num_of_thread: int = typer.Option(
        1, "--num-of-thread", help="Number of crawling threads"
    ),
    interval_time: int = typer.Option(
        10000, "--interval-time", help="Crawling interval time (ms)"
    ),
    boost: float = typer.Option(1.0, "--boost", help="Boost value"),
    available: bool = typer.Option(
        True, "--available", help="Availability (true/false)"
    ),
    sort_order: int = typer.Option(1, "--sort-order", help="Sort order"),
    description: str = typer.Option("", "--description", help="Description"),
    label_type_ids: List[str] = typer.Option(
        [], "--label-type-id", help="Label type IDs"
    ),
    included_urls: List[str] = typer.Option([], "--included-url", help="Included URLs"),
    excluded_urls: List[str] = typer.Option(
        ["(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico|exe)"],
        "--excluded-url",
        help="Excluded URLs",
    ),
    included_doc_urls: List[str] = typer.Option(
        [], "--included-doc-url", help="Included document URLs"
    ),
    excluded_doc_urls: List[str] = typer.Option(
        [], "--excluded-doc-url", help="Excluded document URLs"
    ),
    config_parameter: List[str] = typer.Option(
        [], "--config-parameter", help="Crawling config parameters"
    ),
    depth: int = typer.Option(1, "--depth", help="Crawling depth"),
    max_access_count: int = typer.Option(
        1000000, "--max-access-count", help="Maximum access count"
    ),
    permissions: List[str] = typer.Option(
        ["{role}guest"], "--permission", help="Access permissions"
    ),
    virtual_hosts: List[str] = typer.Option([], "--virtual-host", help="Virtual hosts"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Create a new WebConfig.
    """
    config = {
        "crud_mode": 1,
        "name": name,
        "urls": "\n".join(urls),
        "user_agent": user_agent,
        "num_of_thread": num_of_thread,
        "interval_time": interval_time,
        "boost": boost,
        "available": available,
        "sort_order": sort_order,
        "description": description,
        "label_type_ids": label_type_ids,
        "included_urls": "\n".join(included_urls),
        "excluded_urls": "\n".join(excluded_urls),
        "included_doc_urls": "\n".join(included_doc_urls),
        "excluded_doc_urls": "\n".join(excluded_doc_urls),
        "config_parameter": "\n".join(config_parameter),
        "depth": depth,
        "max_access_count": max_access_count,
        "permissions": "\n".join(permissions),
        "virtual_hosts": "\n".join(virtual_hosts),
        "created_by": created_by,
        "created_time": created_time,
    }

    _handle_response(
        client.create_webconfig(config),
        output,
        success_message="WebConfig created successfully.",
    )


@webconfig_app.command("update")
def update_webconfig(
    config_id: str = typer.Argument(..., help="WebConfig ID"),
    name: str | None = typer.Option(None, "--name", help="WebConfig name"),
    urls: List[str] | None = typer.Option(None, "--url", help="Crawling target URLs"),
    user_agent: str | None = typer.Option(
        None, "--user-agent", help="User agent string"
    ),
    num_of_thread: int | None = typer.Option(
        None, "--num-of-thread", help="Number of crawling threads"
    ),
    interval_time: int | None = typer.Option(
        None, "--interval-time", help="Crawling interval time (ms)"
    ),
    boost: float | None = typer.Option(None, "--boost", help="Boost value"),
    available: bool | None = typer.Option(
        None, "--available", help="Availability (true/false)"
    ),
    sort_order: int | None = typer.Option(None, "--sort-order", help="Sort order"),
    description: str | None = typer.Option(None, "--description", help="Description"),
    label_type_ids: List[str] | None = typer.Option(
        None, "--label-type-id", help="Label type IDs"
    ),
    included_urls: List[str] | None = typer.Option(
        None, "--included-url", help="Included URLs"
    ),
    excluded_urls: List[str] | None = typer.Option(
        None,
        "--excluded-url",
        help="Excluded URLs",
    ),
    included_doc_urls: List[str] | None = typer.Option(
        None, "--included-doc-url", help="Included document URLs"
    ),
    excluded_doc_urls: List[str] | None = typer.Option(
        None, "--excluded-doc-url", help="Excluded document URLs"
    ),
    config_parameter: List[str] | None = typer.Option(
        None, "--config-parameter", help="Crawling config parameters"
    ),
    depth: int | None = typer.Option(None, "--depth", help="Crawling depth"),
    max_access_count: int | None = typer.Option(
        None, "--max-access-count", help="Maximum access count"
    ),
    permissions: List[str] | None = typer.Option(
        None, "--permission", help="Access permissions"
    ),
    virtual_hosts: List[str] | None = typer.Option(
        None, "--virtual-host", help="Virtual hosts"
    ),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)",
    ),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Update an existing WebConfig.
    """
    result = client.get_webconfig(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.secho(
            f"WebConfig with ID '{config_id}' not found. {message}",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    config = result.get("response", {}).get("setting", {})
    config["crud_mode"] = 2
    config["updated_by"] = updated_by
    config["updated_time"] = updated_time

    if name is not None:
        config["name"] = name
    if urls is not None:
        config["urls"] = "\n".join(urls)
    if user_agent is not None:
        config["user_agent"] = user_agent
    if num_of_thread is not None:
        config["num_of_thread"] = num_of_thread
    if interval_time is not None:
        config["interval_time"] = interval_time
    if boost is not None:
        config["boost"] = boost
    if available is not None:
        config["available"] = available
    if sort_order is not None:
        config["sort_order"] = sort_order
    if description is not None:
        config["description"] = description
    if label_type_ids is not None:
        config["label_type_ids"] = label_type_ids
    if included_urls is not None:
        config["included_urls"] = "\n".join(included_urls)
    if excluded_urls is not None:
        config["excluded_urls"] = "\n".join(excluded_urls)
    if included_doc_urls is not None:
        config["included_doc_urls"] = "\n".join(included_doc_urls)
    if excluded_doc_urls is not None:
        config["excluded_doc_urls"] = "\n".join(excluded_doc_urls)
    if config_parameter is not None:
        config["config_parameter"] = "\n".join(config_parameter)
    if depth is not None:
        config["depth"] = depth
    if max_access_count is not None:
        config["max_access_count"] = max_access_count
    if permissions is not None:
        config["permissions"] = "\n".join(permissions)
    if virtual_hosts is not None:
        config["virtual_hosts"] = "\n".join(virtual_hosts)

    _handle_response(
        client.update_webconfig(config),
        output,
        success_message="WebConfig updated successfully.",
    )


@webconfig_app.command("delete")
def delete_webconfig(
    config_id: str = typer.Argument(..., help="WebConfig ID"),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Delete a WebConfig by ID.
    """
    _handle_response(
        client.delete_webconfig(config_id),
        output,
        success_message=f"WebConfig '{config_id}' deleted successfully.",
    )


@webconfig_app.command("get")
def get_webconfig(
    config_id: str = typer.Argument(..., help="WebConfig ID"),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Retrieve a WebConfig by ID.
    """
    result = client.get_webconfig(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            webconfig = result.get("response", {}).get("setting", {})
            console = Console()
            table = Table(title=f"WebConfig Details: {webconfig.get('name', '-')}")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            # Output all fields (public names)
            table.add_row("id", str(webconfig.get("id", "-")))
            table.add_row("updated_by", str(webconfig.get("updated_by", "-")))
            table.add_row("updated_time", str(webconfig.get("updated_time", "-")))
            table.add_row("version_no", str(webconfig.get("version_no", "-")))
            table.add_row(
                "label_type_ids", "\n".join(webconfig.get("label_type_ids", []))
            )
            table.add_row("crud_mode", str(webconfig.get("crud_mode", "-")))
            table.add_row("name", str(webconfig.get("name", "-")))
            table.add_row("description", str(webconfig.get("description", "-")))
            table.add_row("urls", str(webconfig.get("urls", "-")))
            table.add_row("included_urls", str(webconfig.get("included_urls", "-")))
            table.add_row("excluded_urls", str(webconfig.get("excluded_urls", "-")))
            table.add_row(
                "included_doc_urls", str(webconfig.get("included_doc_urls", "-"))
            )
            table.add_row(
                "excluded_doc_urls", str(webconfig.get("excluded_doc_urls", "-"))
            )
            table.add_row(
                "config_parameter", str(webconfig.get("config_parameter", "-"))
            )
            table.add_row("depth", str(webconfig.get("depth", "-")))
            table.add_row(
                "max_access_count", str(webconfig.get("max_access_count", "-"))
            )
            table.add_row("user_agent", str(webconfig.get("user_agent", "-")))
            table.add_row("num_of_thread", str(webconfig.get("num_of_thread", "-")))
            table.add_row("interval_time", str(webconfig.get("interval_time", "-")))
            table.add_row("boost", str(webconfig.get("boost", "-")))
            table.add_row("available", str(webconfig.get("available", "-")))
            table.add_row("permissions", str(webconfig.get("permissions", "-")))
            table.add_row("virtual_hosts", str(webconfig.get("virtual_hosts", "-")))
            table.add_row("sort_order", str(webconfig.get("sort_order", "-")))
            table.add_row("created_by", str(webconfig.get("created_by", "-")))
            table.add_row("created_time", str(webconfig.get("created_time", "-")))

            console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to retrieve WebConfig. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


@webconfig_app.command("list")
def list_webconfigs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    List WebConfigs.
    """
    result = client.list_webconfigs(page=page, size=size)
    status = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            webconfigs = result.get("response", {}).get("settings", [])
            if not webconfigs:
                typer.secho("No WebConfigs found.", fg=typer.colors.YELLOW)
            else:
                console = Console()
                table = Table(title="WebConfigs")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("NAME", style="cyan", no_wrap=True)
                table.add_column("AVAILABLE", style="cyan", no_wrap=True)
                table.add_column("SORT ORDER", style="cyan", no_wrap=True)
                for webconfig in webconfigs:
                    table.add_row(
                        webconfig.get("id", "-"),
                        webconfig.get("name", "-"),
                        webconfig.get("available", "-"),
                        str(webconfig.get("sort_order", "-")),
                    )
                console.print(table)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Failed to list WebConfigs. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)


def _handle_response(result: dict, output: str, success_message: Optional[str] = None):
    """
    Handle API response output.
    """
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            if success_message:
                typer.secho(success_message, fg=typer.colors.GREEN)
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.secho(
                f"Operation failed. {message} Status code: {status}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=status)
