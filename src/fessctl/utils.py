import base64
import json
from datetime import datetime, timezone
from typing import Optional

import typer
import yaml


def to_utc_iso8601(epoch_millis: Optional[int | str]) -> str:
    if epoch_millis is None:
        return "-"
    dt = datetime.fromtimestamp(int(epoch_millis) / 1000, tz=timezone.utc)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def encode_to_urlsafe_base64(text: str) -> str:
    """
    Converts the specified string to a UTF-8 byte array,
    performs URL-safe Base64 encoding, and returns the result as a string.
    """
    byte_data = text.encode('utf-8')
    encoded_bytes = base64.urlsafe_b64encode(byte_data)
    return encoded_bytes.decode('utf-8')


def _escape_cell(value) -> str:
    if value is None:
        return "-"
    s = str(value)
    s = s.replace("|", "\\|")
    s = s.replace("\n", "<br>")
    return s


def format_list_markdown(title: str, items: list[dict], columns: list[tuple[str, str]]) -> str:
    lines = [f"## {title}", ""]
    headers = [col[0] for col in columns]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for item in items:
        row = []
        for _, key in columns:
            row.append(_escape_cell(item.get(key)))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def format_detail_markdown(title: str, data: dict, fields: list[tuple[str, str]],
                           transforms: dict[str, callable] | None = None) -> str:
    lines = [f"## {title}", ""]
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    for display_name, dict_key in fields:
        value = data.get(dict_key)
        if transforms and dict_key in transforms:
            value = transforms[dict_key](value)
        lines.append(f"| {_escape_cell(display_name)} | {_escape_cell(value)} |")
    return "\n".join(lines)


def format_result_markdown(success: bool, message: str, resource_type: str,
                           action: str, resource_id: str = "") -> str:
    status = "success" if success else "error"
    lines = ["## Result", ""]
    lines.append(f"- **status**: {status}")
    lines.append(f"- **action**: {action}")
    lines.append(f"- **resource_type**: {resource_type}")
    if resource_id:
        lines.append(f"- **id**: {resource_id}")
    lines.append(f"- **message**: {message}")
    return "\n".join(lines)


def output_error(output: str, error: Exception, resource_type: str, action: str):
    if output == "json":
        typer.echo(json.dumps({
            "status": "error",
            "resource_type": resource_type,
            "action": action,
            "message": str(error),
        }, indent=2))
    elif output == "yaml":
        typer.echo(yaml.dump({
            "status": "error",
            "resource_type": resource_type,
            "action": action,
            "message": str(error),
        }))
    else:
        typer.echo(format_result_markdown(False, str(error), resource_type, action))