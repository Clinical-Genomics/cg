"""Module for archiving and retrieving folders via DDN Dataflow."""
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

from pydantic.v1 import BaseModel
from requests.models import Response

from datetime import datetime
from cg.constants.constants import APIMethods, FileFormat
from cg.exc import DdnDataflowAuthenticationError
from cg.io.controller import APIRequest, ReadStream
from cg.models.cg_config import DDNDataFlowConfig

OSTYPE: str = "Unix/MacOS"
ROOT_TO_TRIM: str = "/home"

DESTINATION_ATTRIBUTE: str = "destination"
SOURCE_ATTRIBUTE: str = "source"


class DataflowEndpoints(str, Enum):
    """Enum containing all DDN dataflow endpoints used."""

    ARCHIVE_FILES = "files/archive"
    GET_AUTH_TOKEN = "auth/token"
    REFRESH_AUTH_TOKEN = "auth/token/refresh"
    RETRIEVE_FILES = "files/retrieve"


class ResponseFields(str, Enum):
    """Enum containing all DDN dataflow endpoints used."""

    ACCESS = "access"
    EXPIRE = "expire"
    REFRESH = "refresh"
    RETRIEVE_FILES = "files/retrieve"


class TransferData(BaseModel):
    """Model for representing a singular object transfer."""

    _metadata = None
    destination: str
    source: str

    def trim_path(self, attribute_to_trim: str):
        """Trims the given attribute (source or destination) from its root directory."""
        setattr(
            self,
            attribute_to_trim,
            f"/{Path(getattr(self, attribute_to_trim)).relative_to(ROOT_TO_TRIM)}",
        )

    def add_repositories(self, source_prefix: str, destination_prefix: str):
        """Prepends the given repositories to the source and destination paths."""
        self.source: str = source_prefix + self.source
        self.destination: str = destination_prefix + self.destination


class TransferPayload(BaseModel):
    """Model for representing a Dataflow transfer task."""

    files_to_transfer: List[TransferData]
    osType: str = OSTYPE
    createFolder: bool = False

    def trim_paths(self, attribute_to_trim: str):
        """Trims the source path from its root directory for all objects in the transfer."""
        for transfer_data in self.files_to_transfer:
            transfer_data.trim_path(attribute_to_trim=attribute_to_trim)

    def add_repositories(self, source_prefix: str, destination_prefix: str):
        """Prepends the given repositories to the source and destination paths all objects in the
        transfer."""
        for transfer_data in self.files_to_transfer:
            transfer_data.add_repositories(
                source_prefix=source_prefix, destination_prefix=destination_prefix
            )

    def dict(self, **kwargs) -> dict:
        """Creates a correctly structured dict to be used as the request payload."""
        payload: dict = super().dict(exclude={"files_to_transfer"})
        payload["pathInfo"] = [transfer_data.dict() for transfer_data in self.files_to_transfer]
        payload["metadataList"] = []
        return payload

    def post_request(self, url: str, headers: dict) -> bool:
        """Sends a request to the given url with, the given headers, and its own content as
        payload."""
        return APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=url,
            headers=headers,
            json=self.dict(),
        ).ok


class AuthPayload(BaseModel):
    """Model representing the payload for an Authentication request."""

    dbName: str
    name: str
    password: str
    superUser: bool = False


class RefreshPayload(BaseModel):
    """Model representing the payload for Auth-token refresh request."""

    refresh: str


class AuthResponse(BaseModel):
    """Model representing th response fields from an access request to the Dataflow API."""

    access: str
    expire: int
    refresh: Optional[str]


class DDNDataFlowApi:
    """Class for archiving and retrieving folders via DDN Dataflow."""

    def __init__(self, config: DDNDataFlowConfig):
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
        if not response.ok:
            raise DdnDataflowAuthenticationError(message=response.content.decode())
        response_content: AuthResponse = AuthResponse(
            **ReadStream.get_content_from_stream(
                file_format=FileFormat.JSON, stream=response.content
            )
        )
        self.refresh_token: str = response_content.refresh
        self.auth_token: str = response_content.access
        self.token_expiration: datetime = datetime.fromtimestamp(response_content.expire)

    def _refresh_auth_token(self) -> None:
        """Updates the auth token by providing the refresh token to the REST-API."""
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url=DataflowEndpoints.REFRESH_AUTH_TOKEN),
            headers=self.headers,
            json=RefreshPayload(refresh=self.refresh_token).dict(),
        )
        response_content: AuthResponse = AuthResponse(
            **ReadStream.get_content_from_stream(
                file_format=FileFormat.JSON, stream=response.content
            )
        )
        self.auth_token: str = response_content.access
        self.token_expiration: datetime = datetime.fromtimestamp(response_content.expire)

    @property
    def auth_header(self) -> Dict[str, str]:
        """Returns an authorization header based on the current auth token, or updates it if
        needed."""
        if datetime.now() > self.token_expiration:
            self._refresh_auth_token()
        return {"Authorization": f"Bearer {self.auth_token}"}

    def archive_folders(self, sources_and_destinations: Dict[Path, Path]) -> bool:
        """Archives all folders provided, to their corresponding destination, as given by sources and destination parameter."""
        transfer_data: List[TransferData] = [
            TransferData(source=source.as_posix(), destination=destination.as_posix())
            for source, destination in sources_and_destinations.items()
        ]
        transfer_request: TransferPayload = TransferPayload(files_to_transfer=transfer_data)
        transfer_request.trim_paths(attribute_to_trim=SOURCE_ATTRIBUTE)
        transfer_request.add_repositories(
            source_prefix=self.local_storage, destination_prefix=self.archive_repository
        )
        return transfer_request.post_request(
            headers=dict(self.headers, **self.auth_header),
            url=urljoin(base=self.url, url=DataflowEndpoints.ARCHIVE_FILES),
        )

    def retrieve_folders(self, sources_and_destinations: Dict[Path, Path]) -> bool:
        """Retrieves all folders provided, to their corresponding destination, as given by the sources and destination parameter."""
        transfer_data: List[TransferData] = [
            TransferData(source=source.as_posix(), destination=destination.as_posix())
            for source, destination in sources_and_destinations.items()
        ]
        transfer_request: TransferPayload = TransferPayload(files_to_transfer=transfer_data)
        transfer_request.trim_paths(attribute_to_trim=DESTINATION_ATTRIBUTE)
        transfer_request.add_repositories(
            source_prefix=self.archive_repository, destination_prefix=self.local_storage
        )
        return transfer_request.post_request(
            headers=dict(self.headers, **self.auth_header),
            url=urljoin(base=self.url, url=DataflowEndpoints.RETRIEVE_FILES),
        )
