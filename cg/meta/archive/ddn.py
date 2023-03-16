"""Module for archiving and retrieving folders via DDN Dataflow."""
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin
from requests.models import Response

from datetime import datetime
from cg.constants.constants import APIMethods, FileFormat
from cg.io.controller import APIRequest, ReadStream
from cg.models.cg_config import DDNConfig


class DDNDataFlowApi:
    """Class for archiving and retrieving folders via DDN Dataflow."""

    def __init__(self, config: DDNConfig):
        self.database_name: str = config.database_name
        self.user: str = config.user
        self.password: str = config.password
        self.url: str = config.url
        self.archive_repository = config.archive_repository
        self.local_storage = config.local_storage
        self.auth_token: str
        self.refresh_token: str
        self.token_expiration: datetime
        self._set_auth_tokens()
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        self.ostype: str = "Unix/MacOS"

    def _set_auth_tokens(self) -> None:
        """Retrieves and sets auth and refresh token from the REST-API."""
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="auth/token"),
            headers=self.headers,
            json={
                "dbName": self.database_name,
                "name": self.user,
                "password": self.password,
                "superUser": False,
            },
        )
        response_content: dict = ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=response.content
        )
        self.refresh_token: str = response_content.get("refresh")
        self.auth_token: str = response_content.get("access")
        self.token_expiration: datetime = datetime.fromtimestamp(response_content.get("expire"))

    def _refresh_auth_token(self) -> None:
        """Updates the auth token by providing the refresh token to the REST-API."""
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="auth/token/refresh"),
            headers=self.headers,
            json={
                "refresh": self.refresh_token,
            },
        )
        response_content: dict = ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=response.content
        )
        self.auth_token: str = response_content.get("access")
        self.token_expiration: datetime = datetime.fromtimestamp(response_content.get("expire"))

    @property
    def auth_header(self) -> Dict[str, str]:
        """Returns an authorization header based on the current auth token, or updates it if needed."""
        if datetime.now() > self.token_expiration:
            self._refresh_auth_token()
        return {"Authorization": f"Bearer {self.auth_token}"}

    def archive_folders(self, sources_and_destinations: Dict[Path, Path]) -> bool:
        """Archives all folders provided, to their corresponding destination, as given by dict."""
        payload: dict = {
            "pathInfo": self._format_paths_archive(
                sources_and_destinations=sources_and_destinations
            ),
            "osType": self.ostype,
            "createFolder": True,
            "metadataList": [],
        }
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="files/archive"),
            headers=dict(self.headers, **self.auth_header),
            json=payload,
        )
        return response.ok

    def retrieve_folders(self, sources_and_destinations: Dict[Path, Path]) -> bool:
        """Retrieves all folders provided, to their corresponding destination, as given by the dict."""
        payload: dict = {
            "pathInfo": self._format_paths_retrieve(
                sources_and_destinations=sources_and_destinations
            ),
            "osType": self.ostype,
            "createFolder": True,
        }
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="files/retrieve"),
            headers=dict(self.headers, **self.auth_header),
            json=payload,
        )
        return response.ok

    def _format_paths_archive(
        self, sources_and_destinations: Dict[Path, Path]
    ) -> List[Dict[str, str]]:
        """Formats the given archiving-dictionary into the data structure specified by the REST-API."""
        return [
            {
                "source": Path(self.local_storage, source.relative_to("/home")).as_posix(),
                "destination": self.archive_repository + destination.as_posix(),
            }
            for source, destination in sources_and_destinations.items()
        ]

    def _format_paths_retrieve(
        self, sources_and_destinations: Dict[Path, Path]
    ) -> List[Dict[str, str]]:
        """Formats the given retrieve-dictionary into the data structure specified by the
        REST-API."""
        return [
            {
                "source": self.archive_repository + source.as_posix(),
                "destination": Path(
                    self.local_storage, destination.relative_to("/home")
                ).as_posix(),
            }
            for source, destination in sources_and_destinations.items()
        ]
