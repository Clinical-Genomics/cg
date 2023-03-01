from pathlib import Path
from typing import Dict
from urllib.parse import urljoin
from requests.models import Response

from datetime import datetime
from cg.constants.constants import APIMethods, FileFormat
from cg.io.controller import APIRequest, ReadStream
from cg.models.cg_config import DDNConfig


class DDNApi:
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

    def _set_auth_tokens(self) -> None:
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="auth/token"),
            headers={"Content-Type": "application/json", "accept": "application/json"},
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
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="auth/token/refresh"),
            headers={"Content-Type": "application/json", "accept": "application/json"},
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
        if datetime.now() > self.token_expiration:
            self._refresh_auth_token()
        return {"Authorization": f"Bearer {self.auth_token}"}

    # Todo add json construction logic here
    def archive_folder(self, destination: Path, source: Path):
        payload: dict = {
            "pathInfo": [self._construct_path_dict(destination=destination, source=source)],
            "osType": "linux",
            "createDirectory": "true",
            "metadataList": [],
        }
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="files/archive"),
            headers=self.auth_header,
            json=payload,
        )

    def retrieve_folder(self, destination: Path, source: Path):
        payload: dict = {
            "pathInfo": [self._construct_path_dict(destination=destination, source=source)],
            "osType": "linux",
            "createDirectory": "true",
        }
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="files/retrieve"),
            headers=self.auth_header,
            json=payload,
        )

    def _construct_path_dict(self, source, destination) -> Dict[str, str]:
        return {
            "source": "archive@OneOne:/Test./ada_event",
            "destination": "nfs@Nas_1:/Miria/Binary/Adm",
        }
