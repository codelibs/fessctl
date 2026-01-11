"""
Unit tests for fessctl.config.settings module.
"""
import os
import pytest

from fessctl.config.settings import Settings


class TestSettings:
    """Tests for the Settings dataclass."""

    def test_default_values(self, monkeypatch):
        """Test that default values are used when environment variables are not set."""
        # Clear any existing environment variables
        monkeypatch.delenv("FESS_ENDPOINT", raising=False)
        monkeypatch.delenv("FESS_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("FESS_VERSION", raising=False)

        settings = Settings()

        assert settings.fess_endpoint == "http://localhost:8080"
        assert settings.access_token is None
        assert settings.fess_version == "15.4.0"

    def test_endpoint_from_environment(self, monkeypatch):
        """Test that FESS_ENDPOINT environment variable is used."""
        monkeypatch.setenv("FESS_ENDPOINT", "http://custom-fess:9200")
        monkeypatch.delenv("FESS_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("FESS_VERSION", raising=False)

        settings = Settings()

        assert settings.fess_endpoint == "http://custom-fess:9200"

    def test_access_token_from_environment(self, monkeypatch):
        """Test that FESS_ACCESS_TOKEN environment variable is used."""
        monkeypatch.delenv("FESS_ENDPOINT", raising=False)
        monkeypatch.setenv("FESS_ACCESS_TOKEN", "my-secret-token")
        monkeypatch.delenv("FESS_VERSION", raising=False)

        settings = Settings()

        assert settings.access_token == "my-secret-token"

    def test_version_from_environment(self, monkeypatch):
        """Test that FESS_VERSION environment variable is used."""
        monkeypatch.delenv("FESS_ENDPOINT", raising=False)
        monkeypatch.delenv("FESS_ACCESS_TOKEN", raising=False)
        monkeypatch.setenv("FESS_VERSION", "14.19.2")

        settings = Settings()

        assert settings.fess_version == "14.19.2"

    def test_all_values_from_environment(self, monkeypatch):
        """Test that all environment variables are used together."""
        monkeypatch.setenv("FESS_ENDPOINT", "http://production-fess:8080")
        monkeypatch.setenv("FESS_ACCESS_TOKEN", "production-token")
        monkeypatch.setenv("FESS_VERSION", "15.3.2")

        settings = Settings()

        assert settings.fess_endpoint == "http://production-fess:8080"
        assert settings.access_token == "production-token"
        assert settings.fess_version == "15.3.2"

    def test_settings_is_frozen(self, monkeypatch):
        """Test that Settings is immutable (frozen dataclass)."""
        monkeypatch.delenv("FESS_ENDPOINT", raising=False)
        monkeypatch.delenv("FESS_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("FESS_VERSION", raising=False)

        settings = Settings()

        with pytest.raises(AttributeError):
            settings.fess_endpoint = "http://new-endpoint:8080"

    def test_empty_access_token_string(self, monkeypatch):
        """Test that empty string for access token is treated as empty string, not None."""
        monkeypatch.delenv("FESS_ENDPOINT", raising=False)
        monkeypatch.setenv("FESS_ACCESS_TOKEN", "")
        monkeypatch.delenv("FESS_VERSION", raising=False)

        settings = Settings()

        # Empty string is still a valid value from environment
        assert settings.access_token == ""

    def test_endpoint_with_trailing_slash(self, monkeypatch):
        """Test endpoint with trailing slash is preserved as-is."""
        monkeypatch.setenv("FESS_ENDPOINT", "http://fess:8080/")
        monkeypatch.delenv("FESS_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("FESS_VERSION", raising=False)

        settings = Settings()

        # The trailing slash should be preserved
        assert settings.fess_endpoint == "http://fess:8080/"

    def test_endpoint_https(self, monkeypatch):
        """Test that HTTPS endpoints work correctly."""
        monkeypatch.setenv("FESS_ENDPOINT", "https://secure-fess.example.com:443")
        monkeypatch.delenv("FESS_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("FESS_VERSION", raising=False)

        settings = Settings()

        assert settings.fess_endpoint == "https://secure-fess.example.com:443"

    def test_version_formats(self, monkeypatch):
        """Test various version format strings."""
        test_versions = ["14.0.0", "15.3.2", "15.4.0", "16.0.0-SNAPSHOT"]
        monkeypatch.delenv("FESS_ENDPOINT", raising=False)
        monkeypatch.delenv("FESS_ACCESS_TOKEN", raising=False)

        for version in test_versions:
            monkeypatch.setenv("FESS_VERSION", version)
            settings = Settings()
            assert settings.fess_version == version
