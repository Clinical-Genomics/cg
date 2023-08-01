from typing import List

from housekeeper.store.models import File
from pydantic.v1 import BaseModel

from cg.store.models import Sample


class FileTransferData(BaseModel):
    @classmethod
    def from_models(cls, file: File, sample: Sample):
        raise NotImplementedError


class ArchiveHandler:
    def archive_folders(self, sources_and_destinations: List[FileTransferData]):
        raise NotImplementedError

    def retrieve_folders(self, sources_and_destinations: List[FileTransferData]):
        raise NotImplementedError
