"""Contains base models to be inherited from in other archive software files."""
from abc import abstractmethod, ABC
from typing import List

from housekeeper.store.models import File
from pydantic import BaseModel

from cg.store.models import Sample


class ArchiveFile(ABC, BaseModel):
    """Base class for classes representing files to be archived."""

    @classmethod
    @abstractmethod
    def from_file_and_sample(cls, file: File, sample: Sample) -> "ArchiveFile":
        """Instantiates the class from a File and Sample object."""
        raise NotImplementedError


class ArchiveInterface(ABC):
    """Base class for classes handling different archiving programs."""

    @abstractmethod
    def archive_folders(self, sources_and_destinations: List[ArchiveFile]):
        """Archives all folders provided, to their corresponding destination,
        as given by sources and destination parameter."""
        raise NotImplementedError

    @abstractmethod
    def retrieve_folders(self, sources_and_destinations: List[ArchiveFile]):
        """Retrieves all folders provided, to their corresponding destination, as given by the
        sources and destination parameter."""
        raise NotImplementedError
