import logging
from typing import Callable, Dict, List, Optional

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.archiving import ArchiveLocations
from cg.meta.archive.ddn_dataflow import DDNDataFlowClient
from cg.meta.archive.models import ArchiveHandler, FileAndSample
from cg.models.cg_config import DataFlowConfig
from cg.store import Store
from cg.store.models import Sample
from housekeeper.store.models import File
from pydantic import BaseModel, ConfigDict

LOG = logging.getLogger(__name__)


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


archive_handlers: Dict[str, Callable] = {ArchiveLocations.KAROLINSKA_BUCKET: DDNDataFlowClient}


class SpringArchiveAPI:
    """Class handling the archiving of sample SPRING files to an off-premise location for long
    term storage."""

    def __init__(
        self, housekeeper_api: HousekeeperAPI, status_db: Store, data_flow_config: DataFlowConfig
    ):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.status_db: Store = status_db
        self.data_flow_config: DataFlowConfig = data_flow_config

    def archive_files(self, files: List[FileAndSample], archive_location: ArchiveLocations) -> int:
        archive_handler: ArchiveHandler = archive_handlers[archive_location](self.data_flow_config)
        return archive_handler.archive_folders(files_and_samples=files)

    def get_sample(self, file: File) -> Optional[Sample]:
        """Fetches the Sample corresponding to a File and logs if a Sample is not found."""
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
