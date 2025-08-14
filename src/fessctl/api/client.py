import json
from enum import Enum
from typing import Dict, List, Optional

import httpx

from fessctl.config.settings import Settings


class Action(Enum):
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    LIST = "list"
    GET = "get"
    START = "start"
    STOP = "stop"


class FessAPIClientError(Exception):
    """
    Exception raised when an HTTP request to Fess fails or the response cannot be parsed as JSON.
    Contains the HTTP status code and the raw response content.
    """

    def __init__(self, status_code: int, content: str):
        self.status_code = status_code
        self.content = content
        super().__init__(f"HTTP {status_code} Error: {content}")


class FessAPIClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.fess_endpoint
        self.admin_api_headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }
        self.search_api_headers = {
            "Content-Type": "application/json",
        }
        self.timeout = 5.0
        self._major_version, self._minor_version = self._parse_version(
            settings.fess_version)

    def _parse_version(self, version: str) -> tuple[int, int]:
        try:
            major_str, minor_str, *_ = version.split(".")
            return int(major_str), int(minor_str)
        except Exception as e:
            raise ValueError(f"Invalid version format: '{version}'") from e

    def send_request(
        self,
        action: Action,
        url: str,
        json_data: dict | None = None,
        params: dict | None = None,
        is_admin: bool = True,
    ) -> dict:
        headers = self.admin_api_headers if is_admin else self.search_api_headers
        try:
            if action == Action.CREATE:
                if self._major_version <= 14:
                    response = httpx.put(
                        url, headers=headers, json=json_data, params=params, timeout=self.timeout
                    )
                else:
                    response = httpx.post(
                        url, headers=headers, json=json_data, params=params, timeout=self.timeout
                    )
            elif action == Action.EDIT:
                if self._major_version <= 14:
                    response = httpx.post(
                        url, headers=headers, json=json_data, params=params, timeout=self.timeout
                    )
                else:
                    response = httpx.put(
                        url, headers=headers, json=json_data, params=params, timeout=self.timeout
                    )
            elif action == Action.DELETE:
                response = httpx.delete(
                    url, headers=headers, params=params, timeout=self.timeout
                )
            elif action == Action.LIST or action == Action.GET:
                response = httpx.get(
                    url, headers=headers, params=params, timeout=self.timeout
                )
            elif action == Action.START or action == Action.STOP:
                if self._major_version <= 14:
                    response = httpx.post(
                        url, headers=headers, json=json_data, params=params, timeout=self.timeout
                    )
                else:
                    response = httpx.put(
                        url, headers=headers, json=json_data, params=params, timeout=self.timeout
                    )
            else:
                raise ValueError("Invalid action specified")
        except httpx.RequestError as e:
            raise FessAPIClientError(
                status_code=-1,
                content=str(e)
            ) from e
        # response.raise_for_status()
        try:
            return response.json()
        except json.decoder.JSONDecodeError as e:
            raw = response.text
            code = response.status_code
            raise FessAPIClientError(
                status_code=code,
                content=raw
            ) from e

    def ping(self) -> dict:
        """
        Sends a GET request to the health endpoint of the API to check the service status.

        Returns:
            dict: The response from the health endpoint, typically containing service health information.
        """
        url = f"{self.base_url}/api/v1/health"
        return self.send_request(Action.GET, url, is_admin=False)

    # Role APIs

    def create_role(
        self, name: str, attributes: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Creates a new role with the specified name and optional attributes.

        Args:
            name (str): The name of the role to be created.
            attributes (Optional[Dict[str, str]]): A dictionary of additional attributes
                to associate with the role. Defaults to None.

        Returns:
            dict: The response from the server after attempting to create the role.
        """
        url = f"{self.base_url}/api/admin/role/setting"
        data = {
            "crud_mode": 1,  # 1 indicates 'create'
            "name": name,
        }
        if attributes:
            data["attributes"] = attributes
        return self.send_request(Action.CREATE, url, json_data=data)

    def update_role(self, config: dict) -> dict:
        """
        Updates an existing role with the provided configuration.

        Args:
            config (dict): A dictionary containing the role configuration to update.

        Returns:
            dict: The response from the server after attempting to update the role.
        """
        url = f"{self.base_url}/api/admin/role/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_role(self, role_id: str) -> dict:
        """
        Deletes a role by its ID.

        Args:
            role_id (str): The ID of the role to delete.

        Returns:
            dict: The response from the server after attempting to delete the role.
        """
        url = f"{self.base_url}/api/admin/role/setting/{role_id}"
        return self.send_request(Action.DELETE, url)

    def get_role(self, role_id: str) -> dict:
        """
        Retrieves the details of a role by its ID.

        Args:
            role_id (str): The ID of the role to retrieve.

        Returns:
            dict: The response from the server containing role details.
        """
        url = f"{self.base_url}/api/admin/role/setting/{role_id}"
        return self.send_request(Action.GET, url)

    def list_roles(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieve a paginated list of roles from the server.

        Args:
            page (int, optional): The page number to retrieve. Defaults to 1.
            size (int, optional): The number of roles per page. Defaults to 100.

        Returns:
            dict: A dictionary containing the response data with the list of roles.

        Raises:
            httpx.HTTPStatusError: If the HTTP request returns an error status code.
        """
        url = f"{self.base_url}/api/admin/role/settings"
        params = {
            "page": page,
            "size": size,
        }
        return self.send_request(Action.LIST, url, params=params)

    # Group APIs

    def create_group(
        self, name: str, attributes: Optional[Dict[str, str]] = None
    ) -> dict:
        """
        Creates a new group with the specified name and optional attributes.

        Args:
            name (str): The name of the group to be created.
            attributes (Optional[Dict[str, str]]): A dictionary of additional attributes
                to associate with the group. Defaults to None.

        Returns:
            dict: The response from the server after attempting to create the group.
        """
        url = f"{self.base_url}/api/admin/group/setting"
        data = {
            "crud_mode": 1,  # 1 indicates 'create'
            "name": name,
        }
        if attributes:
            data["attributes"] = attributes
        return self.send_request(Action.CREATE, url, json_data=data)

    def update_group(self, config: dict) -> dict:
        """
        Updates an existing group with the provided configuration.
        Args:
            config (dict): A dictionary containing the group configuration to update.
        Returns:
            dict: The response from the server after attempting to update the group.
        """
        url = f"{self.base_url}/api/admin/group/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_group(self, group_id: str) -> dict:
        """
        Deletes a group by its ID.

        Args:
            group_id (str): The ID of the group to delete.

        Returns:
            dict: The response from the server after attempting to delete the group.
        """
        url = f"{self.base_url}/api/admin/group/setting/{group_id}"
        return self.send_request(Action.DELETE, url)

    def get_group(self, group_id: str) -> dict:
        """
        Retrieves the details of a group by its ID.

        Args:
            group_id (str): The ID of the group to retrieve.

        Returns:
            dict: The response from the server containing group details.
        """
        url = f"{self.base_url}/api/admin/group/setting/{group_id}"
        return self.send_request(Action.GET, url)

    def list_groups(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieve a paginated list of groups from the server.

        Args:
            page (int, optional): The page number to retrieve. Defaults to 1.
            size (int, optional): The number of groups per page. Defaults to 100.

        Returns:
            dict: A dictionary containing the response data with the list of groups.

        Raises:
            httpx.HTTPStatusError: If the HTTP request returns an error status code.
        """
        url = f"{self.base_url}/api/admin/group/settings"
        params = {
            "page": page,
            "size": size,
        }
        return self.send_request(Action.LIST, url, params=params)

    # User APIs

    def create_user(
        self,
        name: str,
        password: Optional[str] = None,
        confirm_password: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
        roles: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
    ) -> dict:
        """
        Creates a new user in the system with the specified details.

        Args:
            name (str): The name of the user to be created.
            password (Optional[str], optional): The password for the user. Defaults to None.
            confirm_password (Optional[str], optional): Confirmation of the password. Defaults to None.
            attributes (Optional[Dict[str, str]], optional): Additional attributes for the user as key-value pairs. Defaults to None.
            roles (Optional[List[str]], optional): A list of roles to assign to the user. Defaults to None.
            groups (Optional[List[str]], optional): A list of groups to assign the user to. Defaults to None.

        Returns:
            dict: The response from the server after attempting to create the user.
        """
        url = f"{self.base_url}/api/admin/user/setting"
        data = {
            "crud_mode": 1,
            "name": name,
        }
        if password:
            data["password"] = password
        if confirm_password:
            data["confirm_password"] = confirm_password
        if attributes:
            data["attributes"] = attributes
        if roles:
            data["roles"] = roles
        if groups:
            data["groups"] = groups
        return self.send_request(Action.CREATE, url, json_data=data)

    def update_user(self, config: dict) -> dict:
        """
        Updates an existing user with the provided configuration.

        Args:
            config (dict): A dictionary containing the user configuration to update.

        Returns:
            dict: The response from the server after attempting to update the user.
        """
        url = f"{self.base_url}/api/admin/user/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_user(self, user_id: str) -> dict:
        """
        Deletes a user by their ID.

        Args:
            user_id (str): The ID of the user to delete.

        Returns:
            dict: The response from the server after attempting to delete the user.
        """
        url = f"{self.base_url}/api/admin/user/setting/{user_id}"
        return self.send_request(Action.DELETE, url)

    def get_user(self, user_id: str) -> dict:
        """
        Retrieves the details of a user by their ID.

        Args:
            user_id (str): The ID of the user to retrieve.

        Returns:
            dict: The response from the server containing user details.
        """
        url = f"{self.base_url}/api/admin/user/setting/{user_id}"
        return self.send_request(Action.GET, url)

    def list_users(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a paginated list of users from the server.

        Args:
            page (int, optional): The page number to retrieve. Defaults to 1.
            size (int, optional): The number of users per page. Defaults to 100.

        Returns:
            dict: A dictionary containing the response data from the server.
        """
        url = f"{self.base_url}/api/admin/user/settings"
        params = {
            "page": page,
            "size": size,
        }
        return self.send_request(Action.LIST, url, params=params)

    # WebConfig APIs

    def create_webconfig(self, config: dict) -> dict:
        """
        Creates a new WebConfig.
        """
        url = f"{self.base_url}/api/admin/webconfig/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_webconfig(self, config: dict) -> dict:
        """
        Updates an existing WebConfig.
        """
        url = f"{self.base_url}/api/admin/webconfig/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_webconfig(self, config_id: str) -> dict:
        """
        Deletes a WebConfig by ID.
        """
        url = f"{self.base_url}/api/admin/webconfig/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_webconfig(self, config_id: str) -> dict:
        """
        Retrieves a WebConfig by ID.
        """
        url = f"{self.base_url}/api/admin/webconfig/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_webconfigs(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of WebConfigs.
        """
        url = f"{self.base_url}/api/admin/webconfig/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # FileConfig APIs

    def create_fileconfig(self, config: dict) -> dict:
        """
        Creates a new FileConfig.
        """
        url = f"{self.base_url}/api/admin/fileconfig/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_fileconfig(self, config: dict) -> dict:
        """
        Updates an existing FileConfig.
        """
        url = f"{self.base_url}/api/admin/fileconfig/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_fileconfig(self, config_id: str) -> dict:
        """
        Deletes a FileConfig by ID.
        """
        url = f"{self.base_url}/api/admin/fileconfig/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_fileconfig(self, config_id: str) -> dict:
        """
        Retrieves a FileConfig by ID.
        """
        url = f"{self.base_url}/api/admin/fileconfig/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_fileconfigs(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of FileConfigs.
        """
        url = f"{self.base_url}/api/admin/fileconfig/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # DataConfig APIs

    def create_dataconfig(self, config: dict) -> dict:
        """
        Creates a new DataConfig.
        """
        url = f"{self.base_url}/api/admin/dataconfig/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_dataconfig(self, config: dict) -> dict:
        """
        Updates an existing DataConfig.
        """
        url = f"{self.base_url}/api/admin/dataconfig/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_dataconfig(self, config_id: str) -> dict:
        """
        Deletes a DataConfig by ID.
        """
        url = f"{self.base_url}/api/admin/dataconfig/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_dataconfig(self, config_id: str) -> dict:
        """
        Retrieves a DataConfig by ID.
        """
        url = f"{self.base_url}/api/admin/dataconfig/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_dataconfigs(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of DataConfigs.
        """
        url = f"{self.base_url}/api/admin/dataconfig/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # Scheduler APIs

    def create_scheduler(self, config: dict) -> dict:
        """
        Creates a new Scheduler.
        """
        url = f"{self.base_url}/api/admin/scheduler/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_scheduler(self, config: dict) -> dict:
        """
        Updates an existing Scheduler.
        """
        url = f"{self.base_url}/api/admin/scheduler/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_scheduler(self, scheduler_id: str) -> dict:
        """
        Deletes a Scheduler by ID.
        """
        url = f"{self.base_url}/api/admin/scheduler/setting/{scheduler_id}"
        return self.send_request(Action.DELETE, url)

    def get_scheduler(self, scheduler_id: str) -> dict:
        """
        Retrieves a Scheduler by ID.
        """
        url = f"{self.base_url}/api/admin/scheduler/setting/{scheduler_id}"
        return self.send_request(Action.GET, url)

    def list_schedulers(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of Schedulers.
        """
        url = f"{self.base_url}/api/admin/scheduler/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    def start_scheduler(self, scheduler_id: str) -> dict:
        """
        Starts a Scheduler by ID.
        """
        url = f"{self.base_url}/api/admin/scheduler/{scheduler_id}/start"
        return self.send_request(Action.START, url)

    def stop_scheduler(self, scheduler_id: str) -> dict:
        """
        Stops a Scheduler by ID.
        """
        url = f"{self.base_url}/api/admin/scheduler/{scheduler_id}/stop"
        return self.send_request(Action.STOP, url)

    # JobLog APIs

    def delete_joblog(self, joblog_id: str) -> dict:
        """
        Deletes a JobLog by ID.
        """
        url = f"{self.base_url}/api/admin/joblog/log/{joblog_id}"
        return self.send_request(Action.DELETE, url)

    def get_joblog(self, joblog_id: str) -> dict:
        """
        Retrieves a JobLog by ID.
        """
        url = f"{self.base_url}/api/admin/joblog/log/{joblog_id}"
        return self.send_request(Action.GET, url)

    def list_joblogs(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of JobLogs.
        """
        url = f"{self.base_url}/api/admin/joblog/logs"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # AccessToken APIs

    def create_accesstoken(self, config: dict) -> dict:
        """
        Creates a new AccessToken.
        """
        url = f"{self.base_url}/api/admin/accesstoken/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_accesstoken(self, config: dict) -> dict:
        """
        Updates an existing AccessToken.
        """
        url = f"{self.base_url}/api/admin/accesstoken/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_accesstoken(self, config_id: str) -> dict:
        """
        Deletes a AccessToken by ID.
        """
        url = f"{self.base_url}/api/admin/accesstoken/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_accesstoken(self, config_id: str) -> dict:
        """
        Retrieves a AccessToken by ID.
        """
        url = f"{self.base_url}/api/admin/accesstoken/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_accesstokens(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of AccessTokens.
        """
        url = f"{self.base_url}/api/admin/accesstoken/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # CrawlingInfo APIs

    def delete_crawlinginfo(self, crawlinginfo_id: str) -> dict:
        """
        Deletes a CrawlingInfo by ID.
        """
        url = f"{self.base_url}/api/admin/crawlinginfo/log/{crawlinginfo_id}"
        return self.send_request(Action.DELETE, url)

    def get_crawlinginfo(self, crawlinginfo_id: str) -> dict:
        """
        Retrieves a CrawlingInfo by ID.
        """
        url = f"{self.base_url}/api/admin/crawlinginfo/log/{crawlinginfo_id}"
        return self.send_request(Action.GET, url)

    def list_crawlinginfos(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of CrawlingInfos.
        """
        url = f"{self.base_url}/api/admin/crawlinginfo/logs"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # WebAuth APIs

    def create_webauth(self, config: dict) -> dict:
        """
        Creates a new WebAuth.
        """
        url = f"{self.base_url}/api/admin/webauth/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_webauth(self, config: dict) -> dict:
        """
        Updates an existing WebAuth.
        """
        url = f"{self.base_url}/api/admin/webauth/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_webauth(self, config_id: str) -> dict:
        """
        Deletes a WebAuth by ID.
        """
        url = f"{self.base_url}/api/admin/webauth/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_webauth(self, config_id: str) -> dict:
        """
        Retrieves a WebAuth by ID.
        """
        url = f"{self.base_url}/api/admin/webauth/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_webauths(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of WebAuths.
        """
        url = f"{self.base_url}/api/admin/webauth/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # FileAuth APIs

    def create_fileauth(self, config: dict) -> dict:
        """
        Creates a new FileAuth.
        """
        url = f"{self.base_url}/api/admin/fileauth/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_fileauth(self, config: dict) -> dict:
        """
        Updates an existing FileAuth.
        """
        url = f"{self.base_url}/api/admin/fileauth/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_fileauth(self, config_id: str) -> dict:
        """
        Deletes a FileAuth by ID.
        """
        url = f"{self.base_url}/api/admin/fileauth/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_fileauth(self, config_id: str) -> dict:
        """
        Retrieves a FileAuth by ID.
        """
        url = f"{self.base_url}/api/admin/fileauth/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_fileauths(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of FileAuths.
        """
        url = f"{self.base_url}/api/admin/fileauth/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # BadWord APIs

    def create_badword(self, config: dict) -> dict:
        """
        Creates a new BadWord.
        """
        url = f"{self.base_url}/api/admin/badword/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_badword(self, config: dict) -> dict:
        """
        Updates an existing BadWord.
        """
        url = f"{self.base_url}/api/admin/badword/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_badword(self, config_id: str) -> dict:
        """
        Deletes a BadWord by ID.
        """
        url = f"{self.base_url}/api/admin/badword/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_badword(self, config_id: str) -> dict:
        """
        Retrieves a BadWord by ID.
        """
        url = f"{self.base_url}/api/admin/badword/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_badwords(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of BadWords.
        """
        url = f"{self.base_url}/api/admin/badword/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # BoostDoc APIs

    def create_boostdoc(self, config: dict) -> dict:
        """
        Creates a new BoostDoc.
        """
        url = f"{self.base_url}/api/admin/boostdoc/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_boostdoc(self, config: dict) -> dict:
        """
        Updates an existing BoostDoc.
        """
        url = f"{self.base_url}/api/admin/boostdoc/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_boostdoc(self, config_id: str) -> dict:
        """
        Deletes a BoostDoc by ID.
        """
        url = f"{self.base_url}/api/admin/boostdoc/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_boostdoc(self, config_id: str) -> dict:
        """
        Retrieves a BoostDoc by ID.
        """
        url = f"{self.base_url}/api/admin/boostdoc/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_boostdocs(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of BoostDocs.
        """
        url = f"{self.base_url}/api/admin/boostdoc/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # DuplicateHost APIs

    def create_duplicatehost(self, config: dict) -> dict:
        """
        Creates a new DuplicateHost.
        """
        url = f"{self.base_url}/api/admin/duplicatehost/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_duplicatehost(self, config: dict) -> dict:
        """
        Updates an existing DuplicateHost.
        """
        url = f"{self.base_url}/api/admin/duplicatehost/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_duplicatehost(self, config_id: str) -> dict:
        """
        Deletes a DuplicateHost by ID.
        """
        url = f"{self.base_url}/api/admin/duplicatehost/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_duplicatehost(self, config_id: str) -> dict:
        """
        Retrieves a DuplicateHost by ID.
        """
        url = f"{self.base_url}/api/admin/duplicatehost/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_duplicatehosts(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of DuplicateHosts.
        """
        url = f"{self.base_url}/api/admin/duplicatehost/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # ElevateWord APIs

    def create_elevateword(self, config: dict) -> dict:
        """
        Creates a new ElevateWord.
        """
        url = f"{self.base_url}/api/admin/elevateword/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_elevateword(self, config: dict) -> dict:
        """
        Updates an existing ElevateWord.
        """
        url = f"{self.base_url}/api/admin/elevateword/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_elevateword(self, config_id: str) -> dict:
        """
        Deletes a ElevateWord by ID.
        """
        url = f"{self.base_url}/api/admin/elevateword/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_elevateword(self, config_id: str) -> dict:
        """
        Retrieves a ElevateWord by ID.
        """
        url = f"{self.base_url}/api/admin/elevateword/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_elevatewords(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of ElevateWords.
        """
        url = f"{self.base_url}/api/admin/elevateword/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # KeyMatch APIs

    def create_keymatch(self, config: dict) -> dict:
        """
        Creates a new KeyMatch.
        """
        url = f"{self.base_url}/api/admin/keymatch/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_keymatch(self, config: dict) -> dict:
        """
        Updates an existing KeyMatch.
        """
        url = f"{self.base_url}/api/admin/keymatch/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_keymatch(self, config_id: str) -> dict:
        """
        Deletes a KeyMatch by ID.
        """
        url = f"{self.base_url}/api/admin/keymatch/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_keymatch(self, config_id: str) -> dict:
        """
        Retrieves a KeyMatch by ID.
        """
        url = f"{self.base_url}/api/admin/keymatch/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_keymatchs(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of KeyMatchs.
        """
        url = f"{self.base_url}/api/admin/keymatch/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # LabelType APIs

    def create_labeltype(self, config: dict) -> dict:
        """
        Creates a new LabelType.
        """
        url = f"{self.base_url}/api/admin/labeltype/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_labeltype(self, config: dict) -> dict:
        """
        Updates an existing LabelType.
        """
        url = f"{self.base_url}/api/admin/labeltype/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_labeltype(self, config_id: str) -> dict:
        """
        Deletes a LabelType by ID.
        """
        url = f"{self.base_url}/api/admin/labeltype/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_labeltype(self, config_id: str) -> dict:
        """
        Retrieves a LabelType by ID.
        """
        url = f"{self.base_url}/api/admin/labeltype/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_labeltypes(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of LabelTypes.
        """
        url = f"{self.base_url}/api/admin/labeltype/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # PathMap APIs

    def create_pathmap(self, config: dict) -> dict:
        """
        Creates a new PathMap.
        """
        url = f"{self.base_url}/api/admin/pathmap/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_pathmap(self, config: dict) -> dict:
        """
        Updates an existing PathMap.
        """
        url = f"{self.base_url}/api/admin/pathmap/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_pathmap(self, config_id: str) -> dict:
        """
        Deletes a PathMap by ID.
        """
        url = f"{self.base_url}/api/admin/pathmap/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_pathmap(self, config_id: str) -> dict:
        """
        Retrieves a PathMap by ID.
        """
        url = f"{self.base_url}/api/admin/pathmap/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_pathmaps(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of PathMaps.
        """
        url = f"{self.base_url}/api/admin/pathmap/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # RelatedContent APIs

    def create_relatedcontent(self, config: dict) -> dict:
        """
        Creates a new RelatedContent.
        """
        url = f"{self.base_url}/api/admin/relatedcontent/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_relatedcontent(self, config: dict) -> dict:
        """
        Updates an existing RelatedContent.
        """
        url = f"{self.base_url}/api/admin/relatedcontent/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_relatedcontent(self, config_id: str) -> dict:
        """
        Deletes a RelatedContent by ID.
        """
        url = f"{self.base_url}/api/admin/relatedcontent/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_relatedcontent(self, config_id: str) -> dict:
        """
        Retrieves a RelatedContent by ID.
        """
        url = f"{self.base_url}/api/admin/relatedcontent/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_relatedcontents(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of RelatedContents.
        """
        url = f"{self.base_url}/api/admin/relatedcontent/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # RelatedQuery APIs

    def create_relatedquery(self, config: dict) -> dict:
        """
        Creates a new RelatedQuery.
        """
        url = f"{self.base_url}/api/admin/relatedquery/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_relatedquery(self, config: dict) -> dict:
        """
        Updates an existing RelatedQuery.
        """
        url = f"{self.base_url}/api/admin/relatedquery/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_relatedquery(self, config_id: str) -> dict:
        """
        Deletes a RelatedQuery by ID.
        """
        url = f"{self.base_url}/api/admin/relatedquery/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_relatedquery(self, config_id: str) -> dict:
        """
        Retrieves a RelatedQuery by ID.
        """
        url = f"{self.base_url}/api/admin/relatedquery/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_relatedqueries(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of RelatedQueries.
        """
        url = f"{self.base_url}/api/admin/relatedquery/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)

    # ReqHeader APIs

    def create_reqheader(self, config: dict) -> dict:
        """
        Creates a new ReqHeader.
        """
        url = f"{self.base_url}/api/admin/reqheader/setting"
        return self.send_request(Action.CREATE, url, json_data=config)

    def update_reqheader(self, config: dict) -> dict:
        """
        Updates an existing ReqHeader.
        """
        url = f"{self.base_url}/api/admin/reqheader/setting"
        return self.send_request(Action.EDIT, url, json_data=config)

    def delete_reqheader(self, config_id: str) -> dict:
        """
        Deletes a ReqHeader by ID.
        """
        url = f"{self.base_url}/api/admin/reqheader/setting/{config_id}"
        return self.send_request(Action.DELETE, url)

    def get_reqheader(self, config_id: str) -> dict:
        """
        Retrieves a ReqHeader by ID.
        """
        url = f"{self.base_url}/api/admin/reqheader/setting/{config_id}"
        return self.send_request(Action.GET, url)

    def list_reqheaders(self, page: int = 1, size: int = 100) -> dict:
        """
        Retrieves a list of ReqHeaders.
        """
        url = f"{self.base_url}/api/admin/reqheader/settings"
        params = {"page": page, "size": size}
        return self.send_request(Action.LIST, url, params=params)
