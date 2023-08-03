import logging
from typing import List, Optional

from housekeeper.store.models import File
from pydantic.v1 import BaseModel, ConfigDict

from cg.apps.cgstats.db.models import Sample
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.archiving import ArchiveLocationsInUse
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi
from cg.store import Store

LOG = logging.getLogger(__name__)


class FileAndSample(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    file: File
    sample: Sample


def get_files_by_archive_location(
    files_and_samples: List[FileAndSample], archive_location: ArchiveLocationsInUse
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
        self, ddn_dataflow_api: DDNDataFlowApi, housekeeper_api: HousekeeperAPI, status_db: Store
    ):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.ddn_api: DDNDataFlowApi = ddn_dataflow_api
        self.status_db: Store = status_db

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
