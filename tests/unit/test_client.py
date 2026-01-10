"""
Unit tests for fessctl.api.client module.
"""
import json
from unittest.mock import Mock, patch, MagicMock

import httpx
import pytest

from fessctl.api.client import FessAPIClient, FessAPIClientError, Action
from fessctl.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create a mock Settings object."""
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://localhost:8080"
    settings.access_token = "test-token"
    settings.fess_version = "15.4.0"
    return settings


@pytest.fixture
def mock_settings_v14():
    """Create a mock Settings object for Fess 14.x."""
    settings = Mock(spec=Settings)
    settings.fess_endpoint = "http://localhost:8080"
    settings.access_token = "test-token"
    settings.fess_version = "14.19.2"
    return settings


@pytest.fixture
def client(mock_settings):
    """Create a FessAPIClient instance with mocked settings."""
    return FessAPIClient(mock_settings)


@pytest.fixture
def client_v14(mock_settings_v14):
    """Create a FessAPIClient instance for Fess 14.x."""
    return FessAPIClient(mock_settings_v14)


class TestFessAPIClientInit:
    """Tests for FessAPIClient initialization."""

    def test_init_with_valid_settings(self, mock_settings):
        """Test client initialization with valid settings."""
        client = FessAPIClient(mock_settings)

        assert client.base_url == "http://localhost:8080"
        assert client.timeout == 5.0
        assert client._major_version == 15
        assert client._minor_version == 4

    def test_init_with_custom_timeout(self, mock_settings):
        """Test client initialization with custom timeout."""
        client = FessAPIClient(mock_settings, timeout=10.0)

        assert client.timeout == 10.0

    def test_init_sets_admin_headers(self, mock_settings):
        """Test that admin headers are properly set."""
        client = FessAPIClient(mock_settings)

        assert client.admin_api_headers["Authorization"] == "Bearer test-token"
        assert client.admin_api_headers["Content-Type"] == "application/json"

    def test_init_sets_search_headers(self, mock_settings):
        """Test that search headers are properly set (no auth)."""
        client = FessAPIClient(mock_settings)

        assert "Authorization" not in client.search_api_headers
        assert client.search_api_headers["Content-Type"] == "application/json"


class TestParseVersion:
    """Tests for the _parse_version method."""

    def test_parse_version_standard_format(self, mock_settings):
        """Test parsing standard version format."""
        mock_settings.fess_version = "15.4.0"
        client = FessAPIClient(mock_settings)

        assert client._major_version == 15
        assert client._minor_version == 4

    def test_parse_version_v14(self, mock_settings):
        """Test parsing version 14.x."""
        mock_settings.fess_version = "14.19.2"
        client = FessAPIClient(mock_settings)

        assert client._major_version == 14
        assert client._minor_version == 19

    def test_parse_version_with_snapshot(self, mock_settings):
        """Test parsing version with SNAPSHOT suffix."""
        mock_settings.fess_version = "16.0.0-SNAPSHOT"
        client = FessAPIClient(mock_settings)

        assert client._major_version == 16
        assert client._minor_version == 0

    def test_parse_version_invalid_format_raises(self, mock_settings):
        """Test that invalid version format raises ValueError."""
        mock_settings.fess_version = "invalid"

        with pytest.raises(ValueError) as exc_info:
            FessAPIClient(mock_settings)

        assert "Invalid version format" in str(exc_info.value)

    def test_parse_version_empty_string_raises(self, mock_settings):
        """Test that empty version string raises ValueError."""
        mock_settings.fess_version = ""

        with pytest.raises(ValueError):
            FessAPIClient(mock_settings)

    def test_parse_version_non_numeric_raises(self, mock_settings):
        """Test that non-numeric version raises ValueError."""
        mock_settings.fess_version = "abc.def.ghi"

        with pytest.raises(ValueError):
            FessAPIClient(mock_settings)


class TestSendRequestHttpMethods:
    """Tests for HTTP method selection based on action and version."""

    @patch("httpx.post")
    def test_create_fess15_uses_post(self, mock_post, client):
        """Test that CREATE action uses POST for Fess 15.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_post.return_value = mock_response

        client.send_request(Action.CREATE, "http://test/api", json_data={"test": "data"})

        mock_post.assert_called_once()

    @patch("httpx.put")
    def test_create_fess14_uses_put(self, mock_put, client_v14):
        """Test that CREATE action uses PUT for Fess 14.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_put.return_value = mock_response

        client_v14.send_request(Action.CREATE, "http://test/api", json_data={"test": "data"})

        mock_put.assert_called_once()

    @patch("httpx.put")
    def test_edit_fess15_uses_put(self, mock_put, client):
        """Test that EDIT action uses PUT for Fess 15.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_put.return_value = mock_response

        client.send_request(Action.EDIT, "http://test/api", json_data={"test": "data"})

        mock_put.assert_called_once()

    @patch("httpx.post")
    def test_edit_fess14_uses_post(self, mock_post, client_v14):
        """Test that EDIT action uses POST for Fess 14.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_post.return_value = mock_response

        client_v14.send_request(Action.EDIT, "http://test/api", json_data={"test": "data"})

        mock_post.assert_called_once()

    @patch("httpx.delete")
    def test_delete_uses_delete(self, mock_delete, client):
        """Test that DELETE action uses DELETE method."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_delete.return_value = mock_response

        client.send_request(Action.DELETE, "http://test/api")

        mock_delete.assert_called_once()

    @patch("httpx.get")
    def test_list_uses_get(self, mock_get, client):
        """Test that LIST action uses GET method."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_get.return_value = mock_response

        client.send_request(Action.LIST, "http://test/api")

        mock_get.assert_called_once()

    @patch("httpx.get")
    def test_get_uses_get(self, mock_get, client):
        """Test that GET action uses GET method."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_get.return_value = mock_response

        client.send_request(Action.GET, "http://test/api")

        mock_get.assert_called_once()

    @patch("httpx.put")
    def test_start_fess15_uses_put(self, mock_put, client):
        """Test that START action uses PUT for Fess 15.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_put.return_value = mock_response

        client.send_request(Action.START, "http://test/api")

        mock_put.assert_called_once()

    @patch("httpx.post")
    def test_start_fess14_uses_post(self, mock_post, client_v14):
        """Test that START action uses POST for Fess 14.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_post.return_value = mock_response

        client_v14.send_request(Action.START, "http://test/api")

        mock_post.assert_called_once()

    @patch("httpx.put")
    def test_stop_fess15_uses_put(self, mock_put, client):
        """Test that STOP action uses PUT for Fess 15.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_put.return_value = mock_response

        client.send_request(Action.STOP, "http://test/api")

        mock_put.assert_called_once()

    @patch("httpx.post")
    def test_stop_fess14_uses_post(self, mock_post, client_v14):
        """Test that STOP action uses POST for Fess 14.x."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_post.return_value = mock_response

        client_v14.send_request(Action.STOP, "http://test/api")

        mock_post.assert_called_once()


class TestSendRequestErrorHandling:
    """Tests for error handling in send_request."""

    @patch("httpx.get")
    def test_network_error_raises_client_error(self, mock_get, client):
        """Test that network errors raise FessAPIClientError."""
        mock_get.side_effect = httpx.RequestError("Connection refused")

        with pytest.raises(FessAPIClientError) as exc_info:
            client.send_request(Action.GET, "http://test/api")

        assert exc_info.value.status_code == -1
        assert "Network error" in exc_info.value.content

    @patch("httpx.get")
    def test_timeout_error_raises_client_error(self, mock_get, client):
        """Test that timeout errors raise FessAPIClientError."""
        mock_get.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(FessAPIClientError) as exc_info:
            client.send_request(Action.GET, "http://test/api")

        assert exc_info.value.status_code == -1

    @patch("httpx.get")
    def test_invalid_json_response_raises_client_error(self, mock_get, client):
        """Test that invalid JSON response raises FessAPIClientError."""
        mock_response = Mock()
        mock_response.json.side_effect = json.decoder.JSONDecodeError("Invalid", "", 0)
        mock_response.status_code = 200
        mock_response.text = "Not JSON"
        mock_get.return_value = mock_response

        with pytest.raises(FessAPIClientError) as exc_info:
            client.send_request(Action.GET, "http://test/api")

        assert "Invalid JSON response" in exc_info.value.content

    @patch("httpx.get")
    def test_returns_json_response(self, mock_get, client):
        """Test that valid JSON response is returned."""
        expected_data = {"response": {"status": 0, "data": "test"}}
        mock_response = Mock()
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response

        result = client.send_request(Action.GET, "http://test/api")

        assert result == expected_data


class TestSendRequestHeaders:
    """Tests for header handling in send_request."""

    @patch("httpx.get")
    def test_admin_request_uses_admin_headers(self, mock_get, client):
        """Test that admin requests use admin headers."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_get.return_value = mock_response

        client.send_request(Action.GET, "http://test/api", is_admin=True)

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-token"

    @patch("httpx.get")
    def test_non_admin_request_uses_search_headers(self, mock_get, client):
        """Test that non-admin requests use search headers (no auth)."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_get.return_value = mock_response

        client.send_request(Action.GET, "http://test/api", is_admin=False)

        call_kwargs = mock_get.call_args[1]
        assert "Authorization" not in call_kwargs["headers"]


class TestFessAPIClientError:
    """Tests for FessAPIClientError exception."""

    def test_error_message_format(self):
        """Test error message formatting."""
        error = FessAPIClientError(status_code=404, content="Not found")

        assert "HTTP 404 Error" in str(error)
        assert "Not found" in str(error)

    def test_error_attributes(self):
        """Test error attributes are accessible."""
        error = FessAPIClientError(status_code=500, content="Server error")

        assert error.status_code == 500
        assert error.content == "Server error"


class TestPingMethod:
    """Tests for the ping method."""

    @patch("httpx.get")
    def test_ping_calls_health_endpoint(self, mock_get, client):
        """Test that ping calls the correct health endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"status": "green"}}
        mock_get.return_value = mock_response

        client.ping()

        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "/api/v1/health" in call_url

    @patch("httpx.get")
    def test_ping_uses_search_headers(self, mock_get, client):
        """Test that ping uses search headers (no auth)."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": {"status": "green"}}
        mock_get.return_value = mock_response

        client.ping()

        call_kwargs = mock_get.call_args[1]
        assert "Authorization" not in call_kwargs["headers"]


class TestRoleAPIs:
    """Tests for Role API methods."""

    @patch("httpx.post")
    def test_create_role_with_name(self, mock_post, client):
        """Test creating a role with just a name."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0, "id": "role-123"}}
        mock_post.return_value = mock_response

        result = client.create_role("admin")

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["name"] == "admin"
        assert call_kwargs["json"]["crud_mode"] == 1

    @patch("httpx.post")
    def test_create_role_with_attributes(self, mock_post, client):
        """Test creating a role with attributes."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0, "id": "role-123"}}
        mock_post.return_value = mock_response

        client.create_role("admin", attributes={"key": "value"})

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["attributes"] == {"key": "value"}

    @patch("httpx.delete")
    def test_delete_role(self, mock_delete, client):
        """Test deleting a role."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_delete.return_value = mock_response

        client.delete_role("role-123")

        call_url = mock_delete.call_args[0][0]
        assert "role-123" in call_url

    @patch("httpx.get")
    def test_get_role(self, mock_get, client):
        """Test getting a role by ID."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0, "setting": {"id": "role-123"}}}
        mock_get.return_value = mock_response

        client.get_role("role-123")

        call_url = mock_get.call_args[0][0]
        assert "role-123" in call_url

    @patch("httpx.get")
    def test_list_roles_with_pagination(self, mock_get, client):
        """Test listing roles with pagination."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0, "settings": []}}
        mock_get.return_value = mock_response

        client.list_roles(page=2, size=50)

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["page"] == 2
        assert call_kwargs["params"]["size"] == 50


class TestSchedulerAPIs:
    """Tests for Scheduler API methods."""

    @patch("httpx.put")
    def test_start_scheduler(self, mock_put, client):
        """Test starting a scheduler."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_put.return_value = mock_response

        client.start_scheduler("scheduler-123")

        call_url = mock_put.call_args[0][0]
        assert "scheduler-123" in call_url
        assert "/start" in call_url

    @patch("httpx.put")
    def test_stop_scheduler(self, mock_put, client):
        """Test stopping a scheduler."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"status": 0}}
        mock_put.return_value = mock_response

        client.stop_scheduler("scheduler-123")

        call_url = mock_put.call_args[0][0]
        assert "scheduler-123" in call_url
        assert "/stop" in call_url
