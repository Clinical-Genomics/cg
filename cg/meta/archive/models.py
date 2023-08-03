"""Contains base models to be inherited from in other archive software files."""
from typing import List

from housekeeper.store.models import File
from pydantic.v1 import BaseModel

from cg.store.models import Sample


class FileTransferData(BaseModel):
    """Base class for classes representing files to be archived."""

    @classmethod
    def from_models(cls, file: File, sample: Sample):
        """Instantiates the class from a File and Sample object."""
        raise NotImplementedError


class ArchiveHandler:
    """Base class for classes handling different archiving programs."""

    def archive_folders(self, sources_and_destinations: List[FileTransferData]):
        """Archives all folders provided, to their corresponding destination,
        as given by sources and destination parameter."""
        raise NotImplementedError

    def retrieve_folders(self, sources_and_destinations: List[FileTransferData]):
        """Retrieves all folders provided, to their corresponding destination, as given by the
        sources and destination parameter."""
        raise NotImplementedError
