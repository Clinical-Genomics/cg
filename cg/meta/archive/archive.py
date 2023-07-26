import logging
from collections import namedtuple
from typing import Dict, List


from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi
from cg.store import Store

LOG = logging.getLogger(__name__)

PathAndSample = namedtuple("PathAndSample", "path sample_internal_id")


class ArchiveAPI:
    """Class handling the archiving of sample SPRING files."""

    def __init__(
        self, ddn_dataflow_api: DDNDataFlowApi, housekeeper_api: HousekeeperAPI, status_db: Store
    ):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.ddn_api: DDNDataFlowApi = ddn_dataflow_api
        self.status_db: Store = status_db

    def sort_files_on_archive_location(
        self,
        file_data: List[PathAndSample],
    ) -> Dict[str, List[PathAndSample]]:
        """Fetches the archiving location from statusdb for each sample and returns a dict of the
        sorted samples."""
        sorted_files: Dict[str, List[PathAndSample]] = {}
        for file in file_data:
            sample = self.status_db.get_sample_by_internal_id(file.sample_internal_id)
            if not sample:
                LOG.warning(
                    f"No sample found in status_db corresponding to sample_id {file.sample_internal_id}."
                    f"Skipping archiving for corresponding file {file.path}."
                )
                continue
            sorted_files.setdefault(sample.archive_location, [])
            sorted_files[sample.archive_location].append(file)
        return sorted_files
