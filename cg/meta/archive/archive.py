import logging
from typing import Callable, Dict, List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.archiving import ArchiveLocations
from cg.meta.archive.ddn_dataflow import DDNDataFlowClient, MiriaFile
from cg.meta.archive.models import ArchiveHandler, FileTransferData
from cg.store import Store
from cg.store.models import Sample
from housekeeper.store.models import File
from pydantic import BaseModel, ConfigDict

LOG = logging.getLogger(__name__)


class FileAndSample(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    file: File
    sample: Sample


class ArchiveModels(BaseModel):
    """Model containing the necessary file and sample information."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    file_model: Callable
    handler: ArchiveHandler


def filter_files_on_archive_location(
    files_and_samples: List[FileAndSample], archive_location: ArchiveLocations
) -> List[FileAndSample]:
    """
    Returns a list of FileAndSample where the associated sample has a specific archive location.
    """
    return [
        file_and_sample
        for file_and_sample in files_and_samples
        if file_and_sample.sample.archive_location == archive_location
    ]


class SpringArchiveAPI:
    """Class handling the archiving of sample SPRING files to an off-premise location for long
    term storage."""

    def __init__(
        self,
        ddn_dataflow_client: DDNDataFlowClient,
        housekeeper_api: HousekeeperAPI,
        status_db: Store,
    ):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.ddn_client: DDNDataFlowClient = ddn_dataflow_client
        self.status_db: Store = status_db
        self.handler_map: Dict[str, ArchiveModels] = {
            ArchiveLocations.KAROLINSKA_BUCKET: ArchiveModels(
                file_model=MiriaFile.from_file_and_sample, handler=self.ddn_client
            )
        }

    def call_corresponding_archiving_method(
        self, files: List[FileTransferData], archive_location: ArchiveLocations
    ) -> int:
        return self.handler_map[archive_location].handler.archive_folders(
            sources_and_destinations=files
        )

    def get_sample(self, file: File) -> Optional[Sample]:
        sample: Optional[Sample] = self.status_db.get_sample_by_internal_id(
            file.version.bundle.name
        )
        if not sample:
            LOG.warning(
                f"No sample found in status_db corresponding to sample_id {file.version.bundle.name}."
                f"Skipping archiving for corresponding file {file.path}."
            )
        return sample

    def add_samples_to_files(self, files_to_archive: List[File]) -> List[FileAndSample]:
        """Fetches the Sample corresponding to each File, instantiates a FileAndSample object and
        adds it to the list which is returned."""
        files_and_samples: List[FileAndSample] = []
        for file in files_to_archive:
            sample: Optional[Sample] = self.get_sample(file)
            if sample:
                files_and_samples.append(FileAndSample(file=file, sample=sample))
        return files_and_samples

    def convert_files_into_transfer_data(
        self, files_and_samples: List[FileAndSample], archive_location: ArchiveLocations
    ) -> List[FileTransferData]:
        return [
            self.handler_map[archive_location].file_model(
                file=file_and_sample.file, sample=file_and_sample.sample
            )
            for file_and_sample in files_and_samples
        ]
