"""Module for archiving and retrieving folders via DDN Dataflow."""
from enum import Enum
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin

from pydantic import BaseModel
from requests.models import Response

from datetime import datetime
from cg.constants.constants import APIMethods, FileFormat
from cg.io.controller import APIRequest, ReadStream
from cg.models.cg_config import DDNConfig


OSTYPE: str = "Unix/MacOS"
ROOT_TO_TRIM: str = "/home"


class DataflowEndpoints(str, Enum):
    """Enum containing all DDN dataflow endpoints used."""

    GET_AUTH_TOKEN = "auth/token"
    REFRESH_AUTH_TOKEN = "auth/token/refresh"
    ARCHIVE_FILES = "files/archive"
    RETRIEVE_FILES = "files/retrieve"


class TransferData(BaseModel):
    source: str
    destination: str
    # TODO: specify what metadata to include here
    _metadata = None

    def correct_source_root(self):
        self.source = f"/{Path(self.source).relative_to(ROOT_TO_TRIM).as_posix()}"

    def correct_destination_root(self):
        self.destination = f"/{Path(self.destination).relative_to(ROOT_TO_TRIM).as_posix()}"

    def add_repositories(self, source_prefix: str, destination_prefix: str):
        self.source = source_prefix + self.source
        self.destination = destination_prefix + self.destination


class TransferPayload(BaseModel):
    files_to_transfer: List[TransferData]
    osType: str = OSTYPE
    createFolder: bool = False

    def correct_source_root(self):
        for transfer_data in self.files_to_transfer:
            transfer_data.correct_source_root()

    def correct_destination_root(self):
        for transfer_data in self.files_to_transfer:
            transfer_data.correct_destination_root()

    def add_repositories(self, source_prefix: str, destination_prefix: str):
        for transfer_data in self.files_to_transfer:
            transfer_data.add_repositories(
                source_prefix=source_prefix, destination_prefix=destination_prefix
            )

    def dict(self, **kwargs) -> dict:
        payload: dict = super().dict(exclude={"files_to_transfer"})
        payload["pathInfo"] = [transfer_data.dict() for transfer_data in self.files_to_transfer]
        payload["metadataList"] = []

        return payload


class AuthPayload(BaseModel):
    dbName: str
    name: str
    password: str
    superUser: bool = False


class RefreshPayload(BaseModel):
    refresh: str


class DDNDataFlowApi:
    """Class for archiving and retrieving folders via DDN Dataflow."""

    def __init__(self, config: DDNConfig):
        self.database_name: str = config.database_name
        self.user: str = config.user
        self.password: str = config.password
        self.url: str = config.url
        self.archive_repository: str = config.archive_repository
        self.local_storage: str = config.local_storage
        self.auth_token: str
        self.refresh_token: str
        self.token_expiration: datetime
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        self._set_auth_tokens()

    def _set_auth_tokens(self) -> None:
        """Retrieves and sets auth and refresh token from the REST-API."""
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url=DataflowEndpoints.GET_AUTH_TOKEN),
            headers=self.headers,
            json=AuthPayload(
                dbName=self.database_name,
                name=self.user,
                password=self.password,
            ).dict(),
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
            url=urljoin(base=self.url, url=DataflowEndpoints.REFRESH_AUTH_TOKEN),
            headers=self.headers,
            json=RefreshPayload(refresh=self.refresh_token).dict(),
        )
        response_content: dict = ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=response.content
        )
        self.auth_token: str = response_content.get("access")
        self.token_expiration: datetime = datetime.fromtimestamp(response_content.get("expire"))

    @property
    def auth_header(self) -> Dict[str, str]:
        """Returns an authorization header based on the current auth token, or updates it if
        needed."""
        if datetime.now() > self.token_expiration:
            self._refresh_auth_token()
        return {"Authorization": f"Bearer {self.auth_token}"}

    def archive_folders(self, sources_and_destinations: Dict[Path, Path]) -> bool:
        """Archives all folders provided, to their corresponding destination, as given by dict."""
        transfer_data: List[TransferData] = [
            TransferData(source=source.as_posix(), destination=destination.as_posix())
            for source, destination in sources_and_destinations.items()
        ]
        payload: TransferPayload = TransferPayload(files_to_transfer=transfer_data)
        payload.correct_source_root()
        payload.add_repositories(
            source_prefix=self.local_storage, destination_prefix=self.archive_repository
        )
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url=DataflowEndpoints.ARCHIVE_FILES),
            headers=dict(self.headers, **self.auth_header),
            json=payload.dict(),
        )
        return response.ok

    def retrieve_folders(self, sources_and_destinations: Dict[Path, Path]) -> bool:
        """Retrieves all folders provided, to their corresponding destination, as given by the
        dict."""
        transfer_data: List[TransferData] = [
            TransferData(source=source.as_posix(), destination=destination.as_posix())
            for source, destination in sources_and_destinations.items()
        ]
        payload: TransferPayload = TransferPayload(files_to_transfer=transfer_data)
        payload.correct_destination_root()
        payload.add_repositories(
            source_prefix=self.archive_repository, destination_prefix=self.local_storage
        )
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url=DataflowEndpoints.RETRIEVE_FILES),
            headers=dict(self.headers, **self.auth_header),
            json=payload.dict(),
        )
        return response.ok
