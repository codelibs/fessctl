"""
Unit tests for fessctl.utils module.
"""
import pytest

from fessctl.utils import (
    to_utc_iso8601,
    encode_to_urlsafe_base64,
    format_list_markdown,
    format_detail_markdown,
    format_result_markdown,
    output_error,
)


class TestToUtcIso8601:
    """Tests for the to_utc_iso8601 function."""

    def test_with_valid_epoch_millis(self):
        epoch_millis = 1705321845000
        result = to_utc_iso8601(epoch_millis)
        assert result == "2024-01-15T12:30:45Z"

    def test_with_zero_epoch(self):
        epoch_millis = 0
        result = to_utc_iso8601(epoch_millis)
        assert result == "1970-01-01T00:00:00Z"

    def test_with_none_returns_dash(self):
        result = to_utc_iso8601(None)
        assert result == "-"

    def test_with_string_epoch(self):
        epoch_millis_str = "1705321845000"
        result = to_utc_iso8601(epoch_millis_str)
        assert result == "2024-01-15T12:30:45Z"

    def test_with_integer_epoch(self):
        epoch_millis = 946684800000
        result = to_utc_iso8601(epoch_millis)
        assert result == "2000-01-01T00:00:00Z"

    def test_iso8601_format_ends_with_z(self):
        result = to_utc_iso8601(1705321845000)
        assert result.endswith("Z")

    def test_iso8601_format_has_t_separator(self):
        result = to_utc_iso8601(1705321845000)
        assert "T" in result

    def test_with_large_epoch(self):
        epoch_millis = 2539424200000
        result = to_utc_iso8601(epoch_millis)
        assert result == "2050-06-21T11:36:40Z"


class TestEncodeToUrlsafeBase64:
    """Tests for the encode_to_urlsafe_base64 function."""

    def test_basic_string(self):
        text = "hello"
        result = encode_to_urlsafe_base64(text)
        assert result == "aGVsbG8="

    def test_empty_string(self):
        text = ""
        result = encode_to_urlsafe_base64(text)
        assert result == ""

    def test_string_with_special_chars(self):
        text = "hello+world/test"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_unicode_string(self):
        text = "こんにちは"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_string_with_spaces(self):
        text = "hello world"
        result = encode_to_urlsafe_base64(text)
        assert result == "aGVsbG8gd29ybGQ="

    def test_urlsafe_no_standard_base64_chars(self):
        text = "subjects?_d"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_numeric_string(self):
        text = "12345"
        result = encode_to_urlsafe_base64(text)
        assert result == "MTIzNDU="

    def test_long_string(self):
        text = "The quick brown fox jumps over the lazy dog"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_string_with_newlines(self):
        text = "line1\nline2\nline3"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_email_address(self):
        text = "user@example.com"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text


class TestFormatListMarkdown:
    """Tests for the format_list_markdown function."""

    def test_empty_list(self):
        result = format_list_markdown("Items", [], [("ID", "id"), ("NAME", "name")])
        assert "## Items" in result
        assert "| ID | NAME |" in result
        # No data rows
        lines = result.strip().split("\n")
        assert len(lines) == 4  # title, blank, header, separator

    def test_single_item(self):
        items = [{"id": "abc123", "name": "Test"}]
        result = format_list_markdown("Items", items, [("ID", "id"), ("NAME", "name")])
        assert "| abc123 | Test |" in result

    def test_multiple_items(self):
        items = [
            {"id": "1", "name": "First"},
            {"id": "2", "name": "Second"},
            {"id": "3", "name": "Third"},
        ]
        result = format_list_markdown("Items", items, [("ID", "id"), ("NAME", "name")])
        assert "| 1 | First |" in result
        assert "| 2 | Second |" in result
        assert "| 3 | Third |" in result

    def test_pipe_escape(self):
        items = [{"id": "1", "name": "a|b"}]
        result = format_list_markdown("Items", items, [("ID", "id"), ("NAME", "name")])
        assert "a\\|b" in result

    def test_none_values(self):
        items = [{"id": "1"}]
        result = format_list_markdown("Items", items, [("ID", "id"), ("NAME", "name")])
        assert "| 1 | - |" in result

    def test_newlines_in_values(self):
        items = [{"id": "1", "name": "line1\nline2"}]
        result = format_list_markdown("Items", items, [("ID", "id"), ("NAME", "name")])
        assert "line1<br>line2" in result


class TestFormatDetailMarkdown:
    """Tests for the format_detail_markdown function."""

    def test_basic_fields(self):
        data = {"id": "abc123", "name": "Test Config"}
        fields = [("id", "id"), ("name", "name")]
        result = format_detail_markdown("Details", data, fields)
        assert "## Details" in result
        assert "| Field | Value |" in result
        assert "| id | abc123 |" in result
        assert "| name | Test Config |" in result

    def test_with_transforms(self):
        data = {"id": "abc123", "updated_time": 1705321845000}
        fields = [("id", "id"), ("updated_time", "updated_time")]
        transforms = {"updated_time": to_utc_iso8601}
        result = format_detail_markdown("Details", data, fields, transforms=transforms)
        assert "2024-01-15T12:30:45Z" in result

    def test_missing_fields(self):
        data = {"id": "abc123"}
        fields = [("id", "id"), ("name", "name")]
        result = format_detail_markdown("Details", data, fields)
        assert "| name | - |" in result


class TestFormatResultMarkdown:
    """Tests for the format_result_markdown function."""

    def test_success(self):
        result = format_result_markdown(True, "Created successfully.", "WebConfig", "create", "abc123")
        assert "## Result" in result
        assert "**status**: success" in result
        assert "**action**: create" in result
        assert "**resource_type**: WebConfig" in result
        assert "**id**: abc123" in result
        assert "**message**: Created successfully." in result

    def test_failure(self):
        result = format_result_markdown(False, "Not found.", "WebConfig", "get")
        assert "**status**: error" in result

    def test_with_resource_id(self):
        result = format_result_markdown(True, "OK", "WebConfig", "create", "id123")
        assert "**id**: id123" in result

    def test_without_resource_id(self):
        result = format_result_markdown(True, "OK", "WebConfig", "delete")
        assert "**id**" not in result


class TestEscapeCellEmptyString:
    """Tests that empty string values are preserved (not replaced with '-')."""

    def test_empty_string_in_list(self):
        items = [{"id": "1", "name": ""}]
        result = format_list_markdown("Items", items, [("ID", "id"), ("NAME", "name")])
        assert "| 1 |  |" in result

    def test_empty_string_in_detail(self):
        data = {"id": "abc", "description": ""}
        fields = [("id", "id"), ("description", "description")]
        result = format_detail_markdown("Details", data, fields)
        assert "| description |  |" in result

    def test_none_still_shows_dash(self):
        items = [{"id": "1", "name": None}]
        result = format_list_markdown("Items", items, [("ID", "id"), ("NAME", "name")])
        assert "| 1 | - |" in result


class TestOutputError:
    """Tests for the output_error helper."""

    def test_json_output(self, capsys):
        import json as json_mod
        try:
            output_error("json", ValueError("test error"), "WebConfig", "create")
        except SystemExit:
            pass
        captured = capsys.readouterr()
        data = json_mod.loads(captured.out)
        assert data["status"] == "error"
        assert data["resource_type"] == "WebConfig"
        assert data["action"] == "create"
        assert data["message"] == "test error"

    def test_yaml_output(self, capsys):
        import yaml as yaml_mod
        try:
            output_error("yaml", RuntimeError("fail"), "Group", "delete")
        except SystemExit:
            pass
        captured = capsys.readouterr()
        data = yaml_mod.safe_load(captured.out)
        assert data["status"] == "error"
        assert data["resource_type"] == "Group"
        assert data["action"] == "delete"
        assert data["message"] == "fail"

    def test_text_output(self, capsys):
        try:
            output_error("text", Exception("boom"), "User", "get")
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert "**status**: error" in captured.out
        assert "**resource_type**: User" in captured.out
        assert "**action**: get" in captured.out
        assert "**message**: boom" in captured.out
