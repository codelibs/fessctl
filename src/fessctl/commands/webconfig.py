import datetime
import json
from typing import List, Optional

import typer
import yaml

from fessctl.api.client import FessAPIClient
from fessctl.config.settings import Settings
from fessctl.utils import format_detail_markdown, format_list_markdown, format_result_markdown, to_utc_iso8601

webconfig_app = typer.Typer()

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
    included_urls: List[str] = typer.Option(
        [], "--included-url", help="Included URLs"),
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
    virtual_hosts: List[str] = typer.Option(
        [], "--virtual-host", help="Virtual hosts"),
    created_by: str = typer.Option("admin", "--created-by", help="Created by"),
    created_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--created-time",
        help="Created time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Create a new WebConfig.
    """
    client = FessAPIClient(Settings())
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

    result = client.create_webconfig(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            config_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"WebConfig '{config_id}' created successfully.", "WebConfig", "create", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Operation failed. {message} Status code: {status}", "WebConfig", "create"))
            raise typer.Exit(code=status)


@webconfig_app.command("update")
def update_webconfig(
    config_id: str = typer.Argument(..., help="WebConfig ID"),
    name: Optional[str] = typer.Option(None, "--name", help="WebConfig name"),
    urls: Optional[List[str]] = typer.Option(
        None, "--url", help="Crawling target URLs"
    ),
    user_agent: Optional[str] = typer.Option(
        None, "--user-agent", help="User agent string"
    ),
    num_of_thread: Optional[int] = typer.Option(
        None, "--num-of-thread", help="Number of crawling threads"
    ),
    interval_time: Optional[int] = typer.Option(
        None, "--interval-time", help="Crawling interval time (ms)"
    ),
    boost: Optional[float] = typer.Option(None, "--boost", help="Boost value"),
    available: Optional[bool] = typer.Option(
        None, "--available", help="Availability (true/false)"
    ),
    sort_order: Optional[int] = typer.Option(
        None, "--sort-order", help="Sort order"),
    description: Optional[str] = typer.Option(
        None, "--description", help="Description"
    ),
    label_type_ids: Optional[List[str]] = typer.Option(
        None, "--label-type-id", help="Label type IDs"
    ),
    included_urls: Optional[List[str]] = typer.Option(
        None, "--included-url", help="Included URLs"
    ),
    excluded_urls: Optional[List[str]] = typer.Option(
        None,
        "--excluded-url",
        help="Excluded URLs",
    ),
    included_doc_urls: Optional[List[str]] = typer.Option(
        None, "--included-doc-url", help="Included document URLs"
    ),
    excluded_doc_urls: Optional[List[str]] = typer.Option(
        None, "--excluded-doc-url", help="Excluded document URLs"
    ),
    config_parameter: Optional[List[str]] = typer.Option(
        None, "--config-parameter", help="Crawling config parameters"
    ),
    depth: Optional[int] = typer.Option(
        None, "--depth", help="Crawling depth"),
    max_access_count: Optional[int] = typer.Option(
        None, "--max-access-count", help="Maximum access count"
    ),
    permissions: Optional[List[str]] = typer.Option(
        None, "--permission", help="Access permissions"
    ),
    virtual_hosts: Optional[List[str]] = typer.Option(
        None, "--virtual-host", help="Virtual hosts"
    ),
    updated_by: str = typer.Option("admin", "--updated-by", help="Updated by"),
    updated_time: int = typer.Option(
        int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        "--updated-time",
        help="Updated time in milliseconds (UTC)",
    ),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Update an existing WebConfig.
    """
    client = FessAPIClient(Settings())
    result = client.get_webconfig(config_id)
    if result.get("response", {}).get("status", 1) != 0:
        message: str = result.get("response", {}).get("message", "")
        typer.echo(format_result_markdown(False, f"WebConfig with ID '{config_id}' not found. {message}", "WebConfig", "update"))
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

    result = client.update_webconfig(config)
    status: int = result.get("response", {}).get("status", 1)
    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            config_id = result.get("response", {}).get("id", "")
            typer.echo(format_result_markdown(True, f"WebConfig '{config_id}' updated successfully.", "WebConfig", "update", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Operation failed. {message} Status code: {status}", "WebConfig", "update"))
            raise typer.Exit(code=status)


@webconfig_app.command("delete")
def delete_webconfig(
    config_id: str = typer.Argument(..., help="WebConfig ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Delete a WebConfig by ID.
    """
    client = FessAPIClient(Settings())
    result = client.delete_webconfig(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            typer.echo(format_result_markdown(True, f"WebConfig '{config_id}' deleted successfully.", "WebConfig", "delete", config_id))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to delete WebConfig. {message} Status code: {status}", "WebConfig", "delete"))
            raise typer.Exit(code=status)


@webconfig_app.command("get")
def get_webconfig(
    config_id: str = typer.Argument(..., help="WebConfig ID"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    Retrieve a WebConfig by ID.
    """
    client = FessAPIClient(Settings())
    result = client.get_webconfig(config_id)
    status = result.get("response", {}).get("status", 1)

    if output == "json":
        typer.echo(json.dumps(result, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump(result))
    else:
        if status == 0:
            webconfig = result.get("response", {}).get("setting", {})
            typer.echo(format_detail_markdown(
                f"WebConfig Details: {webconfig.get('name', '-')}",
                webconfig,
                [
                    ("id", "id"),
                    ("updated_by", "updated_by"),
                    ("updated_time", "updated_time"),
                    ("version_no", "version_no"),
                    ("label_type_ids", "label_type_ids"),
                    ("crud_mode", "crud_mode"),
                    ("name", "name"),
                    ("description", "description"),
                    ("urls", "urls"),
                    ("included_urls", "included_urls"),
                    ("excluded_urls", "excluded_urls"),
                    ("included_doc_urls", "included_doc_urls"),
                    ("excluded_doc_urls", "excluded_doc_urls"),
                    ("config_parameter", "config_parameter"),
                    ("depth", "depth"),
                    ("max_access_count", "max_access_count"),
                    ("user_agent", "user_agent"),
                    ("num_of_thread", "num_of_thread"),
                    ("interval_time", "interval_time"),
                    ("boost", "boost"),
                    ("available", "available"),
                    ("permissions", "permissions"),
                    ("virtual_hosts", "virtual_hosts"),
                    ("sort_order", "sort_order"),
                    ("created_by", "created_by"),
                    ("created_time", "created_time"),
                ],
                transforms={"updated_time": to_utc_iso8601, "created_time": to_utc_iso8601},
            ))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to retrieve WebConfig. {message} Status code: {status}", "WebConfig", "get"))
            raise typer.Exit(code=status)


@webconfig_app.command("list")
def list_webconfigs(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    size: int = typer.Option(100, "--size", "-s", help="Page size"),
    output: str = typer.Option(
        "text", "--output", "-o", help="Output format (text, json, yaml)"),
):
    """
    List WebConfigs.
    """
    client = FessAPIClient(Settings())
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
                typer.echo("No WebConfigs found.")
            else:
                typer.echo(format_list_markdown("WebConfigs", webconfigs, [
                    ("ID", "id"), ("NAME", "name"), ("AVAILABLE", "available"), ("SORT ORDER", "sort_order"),
                ]))
        else:
            message: str = result.get("response", {}).get("message", "")
            typer.echo(format_result_markdown(False, f"Failed to list WebConfigs. {message} Status code: {status}", "WebConfig", "list"))
            raise typer.Exit(code=status)
