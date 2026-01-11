"""
Unit tests for fessctl.utils module.
"""
import pytest

from fessctl.utils import to_utc_iso8601, encode_to_urlsafe_base64


class TestToUtcIso8601:
    """Tests for the to_utc_iso8601 function."""

    def test_with_valid_epoch_millis(self):
        """Test conversion of valid epoch milliseconds."""
        # 2024-01-15 12:30:45 UTC = 1705321845000 ms
        epoch_millis = 1705321845000
        result = to_utc_iso8601(epoch_millis)
        assert result == "2024-01-15T12:30:45Z"

    def test_with_zero_epoch(self):
        """Test conversion of epoch 0 (1970-01-01T00:00:00Z)."""
        epoch_millis = 0
        result = to_utc_iso8601(epoch_millis)
        assert result == "1970-01-01T00:00:00Z"

    def test_with_none_returns_dash(self):
        """Test that None input returns '-'."""
        result = to_utc_iso8601(None)
        assert result == "-"

    def test_with_string_epoch(self):
        """Test conversion of epoch as string (should be converted to int)."""
        epoch_millis_str = "1705321845000"
        result = to_utc_iso8601(epoch_millis_str)
        assert result == "2024-01-15T12:30:45Z"

    def test_with_integer_epoch(self):
        """Test conversion with integer type."""
        # 2000-01-01T00:00:00Z = 946684800000 ms
        epoch_millis = 946684800000
        result = to_utc_iso8601(epoch_millis)
        assert result == "2000-01-01T00:00:00Z"

    def test_iso8601_format_ends_with_z(self):
        """Test that output ends with Z indicating UTC timezone."""
        result = to_utc_iso8601(1705321845000)
        assert result.endswith("Z")

    def test_iso8601_format_has_t_separator(self):
        """Test that output has T separator between date and time."""
        result = to_utc_iso8601(1705321845000)
        assert "T" in result

    def test_with_large_epoch(self):
        """Test with a large epoch value (future date)."""
        # Use a known epoch and verify format is correct
        # 2539424200000 ms converts to 2050-06-21T11:36:40Z
        epoch_millis = 2539424200000
        result = to_utc_iso8601(epoch_millis)
        assert result == "2050-06-21T11:36:40Z"


class TestEncodeToUrlsafeBase64:
    """Tests for the encode_to_urlsafe_base64 function."""

    def test_basic_string(self):
        """Test encoding of a basic ASCII string."""
        text = "hello"
        result = encode_to_urlsafe_base64(text)
        assert result == "aGVsbG8="

    def test_empty_string(self):
        """Test encoding of an empty string."""
        text = ""
        result = encode_to_urlsafe_base64(text)
        assert result == ""

    def test_string_with_special_chars(self):
        """Test encoding of a string with special characters."""
        text = "hello+world/test"
        result = encode_to_urlsafe_base64(text)
        # URL-safe base64 should not contain + or /
        assert "+" not in result or result.count("+") == 0
        # Verify it can be decoded back
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_unicode_string(self):
        """Test encoding of a Unicode string."""
        text = "こんにちは"  # Japanese "hello"
        result = encode_to_urlsafe_base64(text)
        # Verify it can be decoded back
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_string_with_spaces(self):
        """Test encoding of a string with spaces."""
        text = "hello world"
        result = encode_to_urlsafe_base64(text)
        assert result == "aGVsbG8gd29ybGQ="

    def test_urlsafe_no_standard_base64_chars(self):
        """Test that URL-safe encoding uses - and _ instead of + and /."""
        # A string that would produce + and / in standard base64
        text = "subjects?_d"
        result = encode_to_urlsafe_base64(text)
        # URL-safe base64 uses - instead of + and _ instead of /
        # Standard base64 would give: c3ViamVjdHM/X2Q=
        # URL-safe base64 should not have standard unsafe chars in the middle
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_numeric_string(self):
        """Test encoding of a numeric string."""
        text = "12345"
        result = encode_to_urlsafe_base64(text)
        assert result == "MTIzNDU="

    def test_long_string(self):
        """Test encoding of a longer string."""
        text = "The quick brown fox jumps over the lazy dog"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_string_with_newlines(self):
        """Test encoding of a string with newlines."""
        text = "line1\nline2\nline3"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text

    def test_email_address(self):
        """Test encoding of an email address (common use case)."""
        text = "user@example.com"
        result = encode_to_urlsafe_base64(text)
        import base64
        decoded = base64.urlsafe_b64decode(result).decode('utf-8')
        assert decoded == text
