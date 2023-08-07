"""Contains base models to be inherited from in other archive software files."""
from abc import abstractmethod
from typing import List

from cg.store.models import Sample
from housekeeper.store.models import File
from pydantic import BaseModel


class FileTransferData(BaseModel):
    """Base class for classes representing files to be archived."""

    @classmethod
    @abstractmethod
    def from_file_and_sample(cls, file: File, sample: Sample) -> "ArchiveFile":
        """Instantiates the class from a File and Sample object."""
        pass


class ArchiveHandler:
    """Base class for classes handling different archiving programs."""

    @abstractmethod
    def archive_folders(self, sources_and_destinations: List[FileTransferData]):
        """Archives all folders provided, to their corresponding destination,
        as given by sources and destination parameter."""
        pass

    @abstractmethod
    def retrieve_folders(self, sources_and_destinations: List[FileTransferData]):
        """Retrieves all folders provided, to their corresponding destination, as given by the
        sources and destination parameter."""
        pass
