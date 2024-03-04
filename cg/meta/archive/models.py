"""Contains base models to be inherited from in other archive software files."""

from abc import abstractmethod

from housekeeper.store.models import File
from pydantic import BaseModel, ConfigDict

from cg.models.cg_config import DataFlowConfig
from cg.store.models import Sample


class FileAndSample(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    file: File
    sample: Sample


class FileTransferData(BaseModel):
    """Base class for classes representing files to be archived."""

    @classmethod
    @abstractmethod
    def create_from_file_and_sample(
        cls, file: File, sample: Sample, is_archiving: bool
    ) -> "FileTransferData":
        """Instantiates the class from a File and Sample object."""
        pass


class ArchiveHandler:
    """Base class for classes handling different archiving programs."""

    @abstractmethod
    def __init__(self, config: DataFlowConfig):
        """Initiates the ArchiveHandler based on the provided configuration."""
        pass

    @abstractmethod
    def archive_file(self, file_and_sample: FileAndSample):
        """Archives all folders provided, to their corresponding destination,
        as given by sources and destination parameter."""
        pass

    @abstractmethod
    def retrieve_files(self, files_and_samples: list[FileAndSample]):
        """Retrieves all files for all samples for the given flowcell."""
        pass

    @abstractmethod
    def convert_into_transfer_data(
        self, files_and_samples: list[FileAndSample], is_archiving: bool = True
    ) -> list[FileTransferData]:
        """Converts the provided files_and_samples into a list of objects formatted for the specific archiving flow."""
        pass

    @abstractmethod
    def is_job_done(self, job_id: int) -> bool:
        """Returns true if job has been completed, false otherwise."""
        pass

    @abstractmethod
    def delete_file(self, file_and_sample: FileAndSample) -> None:
        """Deletes a file at the archive location."""
