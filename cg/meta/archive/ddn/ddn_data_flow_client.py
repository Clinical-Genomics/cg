"""Module for archiving and retrieving folders via DDN Dataflow."""

import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from housekeeper.store.models import File
from pydantic import BaseModel
from requests import Response

from cg.exc import ArchiveJobFailedError, DdnDataflowAuthenticationError, DdnDataflowDeleteFileError
from cg.io.api import get, post
from cg.meta.archive.ddn.constants import (
    DELETE_FILE_SUCCESSFUL_MESSAGE,
    DESTINATION_ATTRIBUTE,
    FAILED_JOB_STATUSES,
    SOURCE_ATTRIBUTE,
    DataflowEndpoints,
    JobStatus,
)
from cg.meta.archive.ddn.models import (
    ArchivalResponse,
    AuthPayload,
    AuthToken,
    DeleteFilePayload,
    DeleteFileResponse,
    GetJobStatusResponse,
    MiriaObject,
    RefreshPayload,
    RetrievalResponse,
    TransferPayload,
)
from cg.meta.archive.ddn.utils import get_metadata, get_request_log
from cg.meta.archive.models import ArchiveHandler, FileAndSample
from cg.models.cg_config import DataFlowConfig

LOG = logging.getLogger(__name__)


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
        auth_token: AuthToken = self._get_auth_token()
        self.refresh_token: str = auth_token.refresh
        self.auth_token: str = auth_token.access
        self.token_expiration: datetime = datetime.fromtimestamp(auth_token.expire)

    def _get_auth_token(self) -> AuthToken:
        """Retrieves auth and refresh token from the REST-API."""
        response: Response = post(
            url=urljoin(base=self.url, url=DataflowEndpoints.GET_AUTH_TOKEN),
            headers=self.headers,
            json=AuthPayload(
                dbName=self.database_name,
                name=self.user,
                password=self.password,
            ).model_dump(),
            verify=False,
        )
        if not response.ok:
            raise DdnDataflowAuthenticationError(message=response.text)
        return AuthToken.model_validate(response.json())

    def _refresh_auth_token(self) -> None:
        """Updates the auth token by providing the refresh token to the REST-API."""
        auth_token: AuthToken = self._get_refreshed_auth_token()
        self.auth_token: str = auth_token.access
        self.token_expiration: datetime = datetime.fromtimestamp(auth_token.expire)

    def _get_refreshed_auth_token(self) -> AuthToken:
        response: Response = post(
            url=urljoin(base=self.url, url=DataflowEndpoints.REFRESH_AUTH_TOKEN),
            headers=self.headers,
            json=RefreshPayload(refresh=self.refresh_token).model_dump(),
            verify=False,
        )
        return AuthToken.model_validate(response.json())

    @property
    def auth_header(self) -> dict[str, str]:
        """Returns an authorization header based on the current auth token, or updates it if
        needed."""
        if datetime.now() > self.token_expiration:
            self._refresh_auth_token()
        return {"Authorization": f"Bearer {self.auth_token}"}

    def archive_file(self, file_and_sample: FileAndSample) -> int:
        """Archives all files provided, to their corresponding destination, as given by sources
        and destination in TransferData. Returns the job ID of the archiving task."""
        miria_file_data: list[MiriaObject] = self.convert_into_transfer_data(
            [file_and_sample], is_archiving=True
        )
        metadata: list[dict] = get_metadata(file_and_sample.sample)
        archival_request: TransferPayload = self.create_transfer_request(
            miria_file_data=miria_file_data, is_archiving_request=True, metadata=metadata
        )
        archival_response: ArchivalResponse = self._archive_file(
            headers=dict(self.headers, **self.auth_header),
            body=archival_request,
        )
        return archival_response.job_id

    def retrieve_files(self, files_and_samples: list[FileAndSample]) -> int:
        """Retrieves the provided files and stores them in the corresponding sample bundle in
        Housekeeper."""
        miria_file_data: list[MiriaObject] = self.convert_into_transfer_data(
            files_and_samples=files_and_samples, is_archiving=False
        )
        retrieval_request: TransferPayload = self.create_transfer_request(
            miria_file_data=miria_file_data, is_archiving_request=False
        )
        retrieval_response: RetrievalResponse = self._retrieve_files(
            headers=dict(self.headers, **self.auth_header),
            body=retrieval_request,
        )
        return retrieval_response.job_id

    def create_transfer_request(
        self,
        miria_file_data: list[MiriaObject],
        is_archiving_request: bool,
        metadata: list[dict] = [],
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

        transfer_request = TransferPayload(
            files_to_transfer=miria_file_data,
            createFolder=is_archiving_request,
            metadataList=metadata,
        )
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

    def is_job_done(self, job_id: int) -> bool:
        """Returns True if the specified job is completed, and false if it is still ongoing.
        Raises:
            ArchiveJobFailedError if the specified job has a failed status."""
        get_job_status_response: GetJobStatusResponse = self._get_job_status(
            headers=dict(self.headers, **self.auth_header), job_id=job_id
        )

        job_status: JobStatus = get_job_status_response.status
        LOG.info(f"Miria returned status {job_status} for job {job_id}")
        if job_status == JobStatus.COMPLETED:
            return True
        if job_status in FAILED_JOB_STATUSES:
            raise ArchiveJobFailedError(f"Job with id {job_id} failed with status {job_status}")
        return False

    @staticmethod
    def get_file_name(file: File) -> str:
        return Path(file.path).name

    def delete_file(self, file_and_sample: FileAndSample) -> None:
        """Deletes the given file via Miria."""
        file_name: str = self.get_file_name(file_and_sample.file)
        sample_id: str = file_and_sample.sample.internal_id
        delete_file_payload = DeleteFilePayload(
            global_path=f"{self.archive_repository}{sample_id}/{file_name}"
        )
        response: Response = self._post_request(
            endpoint=DataflowEndpoints.DELETE_FILE,
            headers=dict(self.headers, **self.auth_header),
            body=delete_file_payload,
        )
        delete_file_response = DeleteFileResponse.model_validate(response.json())
        if delete_file_response.message != DELETE_FILE_SUCCESSFUL_MESSAGE:
            raise DdnDataflowDeleteFileError(
                f"Deletion failed with message {delete_file_response.message}"
            )

    def _archive_file(self, body: BaseModel, headers: dict) -> ArchivalResponse:
        """Archives a file via DDN and validates the response."""
        response: Response = self._post_request(
            body=body, endpoint=DataflowEndpoints.ARCHIVE_FILES, headers=headers
        )
        return ArchivalResponse.model_validate(response.json())

    def _retrieve_files(self, body: BaseModel, headers: dict) -> RetrievalResponse:
        """Retrieves files specified in the body and validates the response."""
        response: Response = self._post_request(
            body=body, endpoint=DataflowEndpoints.RETRIEVE_FILES, headers=headers
        )
        return RetrievalResponse.model_validate(response.json())

    def _post_request(
        self, body: BaseModel, endpoint: DataflowEndpoints, headers: dict
    ) -> Response:
        """Posts a request with the provided body and headers to the given endpoint."""
        LOG.info(get_request_log(body=body.model_dump(by_alias=True)))
        response: Response = post(
            url=urljoin(self.url, endpoint),
            headers=headers,
            json=body.model_dump(by_alias=True),
            verify=False,
        )
        response.raise_for_status()
        return response

    def _get_job_status(self, headers: dict, job_id: int) -> GetJobStatusResponse:
        """Gets the job status for the provided job_id."""
        LOG.info(f"Sending GET request for job {job_id}")
        url: str = urljoin(self.url, DataflowEndpoints.GET_JOB_STATUS + str(job_id))
        response: Response = get(
            url=url,
            headers=headers,
            json={},
            verify=False,
        )
        response.raise_for_status()
        return GetJobStatusResponse.model_validate(response.json())
