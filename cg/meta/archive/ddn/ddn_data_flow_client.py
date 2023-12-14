"""Module for archiving and retrieving folders via DDN Dataflow."""
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from housekeeper.store.models import File
from requests import Response

from cg.constants.constants import APIMethods
from cg.exc import ArchiveJobFailedError, DdnDataflowAuthenticationError
from cg.io.controller import APIRequest
from cg.meta.archive.ddn.constants import (
    DESTINATION_ATTRIBUTE,
    FAILED_JOB_STATUSES,
    SOURCE_ATTRIBUTE,
    DataflowEndpoints,
    JobStatus,
)
from cg.meta.archive.ddn.models import (
    AuthPayload,
    AuthToken,
    DeleteFilePayload,
    GetJobStatusPayload,
    GetJobStatusResponse,
    MiriaObject,
    RefreshPayload,
    TransferPayload,
)
from cg.meta.archive.models import ArchiveHandler, FileAndSample, SampleAndDestination
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
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
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
        response: Response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
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

        transfer_request = TransferPayload(
            files_to_transfer=miria_file_data, createFolder=is_archiving_request
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
        get_job_status_payload = GetJobStatusPayload(id=job_id)
        get_job_status_response: GetJobStatusResponse = get_job_status_payload.get_job_status(
            url=urljoin(self.url, DataflowEndpoints.GET_JOB_STATUS + str(job_id)),
            headers=dict(self.headers, **self.auth_header),
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
        delete_file_payload.delete_file(
            url=urljoin(self.url, DataflowEndpoints.DELETE_FILE),
            headers=dict(self.headers, **self.auth_header),
        )
