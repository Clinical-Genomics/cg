import logging
from pathlib import Path

from housekeeper.store.models import File
from pydantic import BaseModel, Field

from cg.meta.archive.ddn.constants import OSTYPE, ROOT_TO_TRIM, JobStatus
from cg.meta.archive.models import FileTransferData
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


def get_request_log(body: dict):
    return "Sending request with body: \n" + f"{body}"


class MiriaObject(FileTransferData):
    """Model for representing a singular object transfer."""

    destination: str
    source: str

    @classmethod
    def create_from_file_and_sample(
        cls, file: File, sample: Sample, is_archiving: bool = True
    ) -> "MiriaObject":
        """Instantiates the class from a File and Sample object."""
        if is_archiving:
            return cls(destination=sample.internal_id, source=file.full_path)
        return cls(
            destination=Path(file.full_path).parent.as_posix(),
            source=Path(sample.internal_id, Path(file.path).name).as_posix(),
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
