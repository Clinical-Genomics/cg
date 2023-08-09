"""Contains base models to be inherited from in other archive software files."""
from abc import abstractmethod
from typing import List

from cg.models.cg_config import DataFlowConfig
from cg.store.models import Sample
from housekeeper.store.models import File
from pydantic import BaseModel
from pydantic.v1 import ConfigDict


class FileAndSample(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    file: File
    sample: Sample


class FileTransferData(BaseModel):
    """Base class for classes representing files to be archived."""

    @classmethod
    @abstractmethod
    def from_file_and_sample(cls, file: File, sample: Sample, is_archiving: bool) -> "ArchiveFile":
        """Instantiates the class from a File and Sample object."""
        pass


class ArchiveHandler:
    """Base class for classes handling different archiving programs."""

    @abstractmethod
    def __init__(self, config: DataFlowConfig):
        """Initiates the ArchiveHandler based on the provided configuration."""
        pass

    @abstractmethod
    def archive_files(self, files_and_samples: List[FileAndSample]):
        """Archives all folders provided, to their corresponding destination,
        as given by sources and destination parameter."""
        pass

    @abstractmethod
    def retrieve_folders(self, sources_and_destinations: List[FileTransferData]):
        """Retrieves all folders provided, to their corresponding destination, as given by the
        sources and destination parameter."""
        pass

    @abstractmethod
    def convert_into_transfer_data(
        self, files_and_samples: List[FileAndSample], is_archiving: bool = True
    ) -> List[FileTransferData]:
        """Converts the provided files_and_samples into a list of objects formatted for the specific archiving flow."""
        pass
