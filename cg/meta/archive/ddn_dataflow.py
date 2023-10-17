"""Module for archiving and retrieving folders via DDN Dataflow."""
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from housekeeper.store.models import File
from pydantic import BaseModel
from requests.models import Response

from cg.constants.constants import APIMethods
from cg.exc import DdnDataflowAuthenticationError
from cg.io.controller import APIRequest
from cg.meta.archive.models import (
    ArchiveHandler,
    FileAndSample,
    FileTransferData,
    SampleAndDestination,
)
from cg.models.cg_config import DataFlowConfig
from cg.store.models import Sample

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


class MiriaObject(FileTransferData):
    """Model for representing a singular object transfer."""

    _metadata = None
    destination: str
    source: str

    @classmethod
    def create_from_file_and_sample(
        cls, file: File, sample: Sample, is_archiving: bool = True
    ) -> "MiriaObject":
        """Instantiates the class from a File and Sample object."""
        if is_archiving:
            return cls(destination=sample.internal_id, source=file.full_path)
        return cls(destination=file.full_path, source=sample.internal_id)

    @classmethod
    def create_from_sample_and_destination(
        cls, sample_and_destination: SampleAndDestination
    ) -> "MiriaObject":
        """Instantiates the class from a SampleAndDestination object,
        i.e. when we want to fetch a folder containing all spring files for said sample."""
        return cls(
            destination=sample_and_destination.destination,
            source=sample_and_destination.sample.internal_id,
        )

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

    files_to_transfer: list[MiriaObject]
    osType: str = OSTYPE
    createFolder: bool = False

    def trim_paths(self, attribute_to_trim: str):
        """Trims the source path from its root directory for all objects in the transfer."""
        for miria_file in self.files_to_transfer:
            miria_file.trim_path(attribute_to_trim=attribute_to_trim)

    def add_repositories(self, source_prefix: str, destination_prefix: str):
        """Prepends the given repositories to the source and destination paths all objects in the
        transfer."""
        for miria_file in self.files_to_transfer:
            miria_file.add_repositories(
                source_prefix=source_prefix, destination_prefix=destination_prefix
            )

    def model_dump(self, **kwargs) -> dict:
        """Creates a correctly structured dict to be used as the request payload."""
        payload: dict = super().model_dump(exclude={"files_to_transfer"})
        payload["pathInfo"] = [miria_file.model_dump() for miria_file in self.files_to_transfer]
        payload["metadataList"] = []
        return payload

    def post_request(self, url: str, headers: dict) -> "TransferJob":
        """Sends a request to the given url with, the given headers, and its own content as payload.

        Arguments:
            url: URL to which the POST goes to.
            headers: Headers which are set in the request
        Raises:
            HTTPError if the response status is not okay.
            ValidationError if the response does not conform to the expected response structure.
        Returns:
            The job ID of the launched transfer task.
        """

        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=url,
            headers=headers,
            json=self.model_dump(),
        )
        response.raise_for_status()
        return TransferJob.model_validate(response.json())


class AuthPayload(BaseModel):
    """Model representing the payload for an Authentication request."""

    dbName: str
    name: str
    password: str
    superUser: bool = False


class RefreshPayload(BaseModel):
    """Model representing the payload for Auth-token refresh request."""

    refresh: str


class AuthToken(BaseModel):
    """Model representing the response fields from an access request to the Dataflow API."""

    access: str
    expire: int
    refresh: Optional[str] = None


class TransferJob(BaseModel):
    """Model representing th response fields of an archive or retrieve reqeust to the Dataflow
    API."""

    job_id: int


class DDNDataFlowClient(ArchiveHandler):
    """Class for archiving and retrieving folders via DDN Dataflow."""

    def __init__(self, config: DataFlowConfig):
        self.database_name: str = config.database_name
        self.user: str = config.user
        self.password: str = config.password
        self.url: str = config.url
        self.archive_repository: str = config.archive_repository
        self.local_storage: str = config.local_storage
        self.auth_token: str
        self.refresh_token: str
        self.token_expiration: datetime
        self.headers: dict[str, str] = {
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
            ).model_dump(),
        )
        if not response.ok:
            raise DdnDataflowAuthenticationError(message=response.text)
        response_content: AuthToken = AuthToken.model_validate(response.json())
        self.refresh_token: str = response_content.refresh
        self.auth_token: str = response_content.access
        self.token_expiration: datetime = datetime.fromtimestamp(response_content.expire)

    def _refresh_auth_token(self) -> None:
        """Updates the auth token by providing the refresh token to the REST-API."""
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url=DataflowEndpoints.REFRESH_AUTH_TOKEN),
            headers=self.headers,
            json=RefreshPayload(refresh=self.refresh_token).model_dump(),
        )
        response_content: AuthToken = AuthToken.model_validate(response.json())
        self.auth_token: str = response_content.access
        self.token_expiration: datetime = datetime.fromtimestamp(response_content.expire)

    @property
    def auth_header(self) -> dict[str, str]:
        """Returns an authorization header based on the current auth token, or updates it if
        needed."""
        if datetime.now() > self.token_expiration:
            self._refresh_auth_token()
        return {"Authorization": f"Bearer {self.auth_token}"}

    def archive_files(self, files_and_samples: list[FileAndSample]) -> int:
        """Archives all files provided, to their corresponding destination, as given by sources
        and destination in TransferData. Returns the job ID of the archiving task."""
        miria_file_data: list[MiriaObject] = self.convert_into_transfer_data(
            files_and_samples, is_archiving=True
        )
        archival_request: TransferPayload = self.create_transfer_request(
            miria_file_data=miria_file_data, is_archiving_request=True
        )
        return archival_request.post_request(
            headers=dict(self.headers, **self.auth_header),
            url=urljoin(base=self.url, url=DataflowEndpoints.ARCHIVE_FILES),
        ).job_id

    def retrieve_samples(self, samples_and_destinations: list[SampleAndDestination]) -> int:
        """Retrieves all archived files for the provided samples and stores them in the specified location in
        Housekeeper."""
        miria_file_data: list[MiriaObject] = []
        for sample_and_housekeeper_destination in samples_and_destinations:
            miria_object: MiriaObject = MiriaObject.create_from_sample_and_destination(
                sample_and_housekeeper_destination
            )
            miria_file_data.append(miria_object)
        retrieval_request: TransferPayload = self.create_transfer_request(
            miria_file_data=miria_file_data, is_archiving_request=False
        )
        return retrieval_request.post_request(
            headers=dict(self.headers, **self.auth_header),
            url=urljoin(base=self.url, url=DataflowEndpoints.RETRIEVE_FILES),
        ).job_id

    def create_transfer_request(
        self, miria_file_data: list[MiriaObject], is_archiving_request: bool
    ) -> TransferPayload:
        """Performs the necessary curation of paths for the request to be valid, depending on if
        it is an archiving or a retrieve request.
        """
        source_prefix: str
        destination_prefix: str
        attribute: str

        source_prefix, destination_prefix, attribute = (
            (self.local_storage, self.archive_repository, SOURCE_ATTRIBUTE)
            if is_archiving_request
            else (self.archive_repository, self.local_storage, DESTINATION_ATTRIBUTE)
        )

        transfer_request: TransferPayload = TransferPayload(files_to_transfer=miria_file_data)
        transfer_request.trim_paths(attribute_to_trim=attribute)
        transfer_request.add_repositories(
            source_prefix=source_prefix, destination_prefix=destination_prefix
        )

        return transfer_request

    def convert_into_transfer_data(
        self, files_and_samples: list[FileAndSample], is_archiving: bool = True
    ) -> list[MiriaObject]:
        """Converts the provided files and samples to the format used for the request."""
        return [
            MiriaObject.create_from_file_and_sample(
                file=file_and_sample.file, sample=file_and_sample.sample, is_archiving=is_archiving
            )
            for file_and_sample in files_and_samples
        ]
