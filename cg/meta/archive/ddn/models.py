import logging

from pydantic import BaseModel, Field

from cg.meta.archive.ddn.constants import OSTYPE, JobStatus

LOG = logging.getLogger(__name__)


def get_request_log(body: dict):
    return "Sending request with body: \n" + f"{body}"


class MiriaObject(BaseModel):
    """Model for representing a singular object transfer."""

    destination: str
    source: str

    def trim_path(self, attribute_to_trim: str):
        """Trims the given attribute (source or destination) from its root directory."""
        pass

    def add_repositories(self, source_prefix: str, destination_prefix: str):
        """Prepends the given repositories to the source and destination paths."""
        self.source: str = source_prefix + self.source
        self.destination: str = destination_prefix + self.destination


class TransferPayload(BaseModel):
    """Model for representing a Dataflow transfer task."""

    files_to_transfer: list[MiriaObject] = Field(..., serialization_alias="pathInfo")
    osType: str = OSTYPE
    createFolder: bool = True
    settings: list[dict] = []
    metadataList: list[dict] = []

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


class ArchivalResponse(BaseModel):
    """Model representing the response fields of an archive request to the Dataflow
    API."""

    job_id: int = Field(alias="jobId")


class RetrievalResponse(BaseModel):
    """Model representing the response fields of a retrieval reqeust to the Dataflow
    API."""

    job_id: int = Field(alias="jobId")


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
    refresh: str | None = None


class GetJobStatusResponse(BaseModel):
    """Model representing the response fields from a get_job_status post."""

    job_id: int = Field(alias="id")
    status: JobStatus


class DeleteFileResponse(BaseModel):
    message: str


class DeleteFilePayload(BaseModel):
    global_path: str
