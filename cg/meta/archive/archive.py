import logging
from collections import namedtuple
from typing import List, Optional

from cg.apps.cgstats.db.models import Sample
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.archiving import ArchiveLocationsInUse
from cg.store import Store

LOG = logging.getLogger(__name__)

PathAndSample = namedtuple("PathAndSample", "path sample_internal_id")


class SpringArchiveAPI:
    """Class handling the archiving of sample SPRING files to an off-premise location for long
    term storage."""

    def __init__(self, housekeeper_api: HousekeeperAPI, status_db: Store):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.status_db: Store = status_db

    def get_files_by_archive_location(
        self, file_data: List[PathAndSample], archive_location: ArchiveLocationsInUse
    ) -> List[PathAndSample]:
        """
        Returns a list of PathAndSample where the associated sample has a specific archive location.
        """
        selected_files: List[PathAndSample] = []
        for file in file_data:
            sample: Optional[Sample] = self.get_sample(file)
            if sample and sample.archive_location == archive_location:
                selected_files.append(file)
        return selected_files

    def get_sample(self, file: PathAndSample) -> Optional[Sample]:
        sample: Optional[Sample] = self.status_db.get_sample_by_internal_id(file.sample_internal_id)
        if not sample:
            LOG.warning(
                f"No sample found in status_db corresponding to sample_id {file.sample_internal_id}."
                f"Skipping archiving for corresponding file {file.path}."
            )
        return sample
