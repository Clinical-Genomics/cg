import logging
from collections import namedtuple
from pathlib import Path
from typing import Dict, List, Optional, Callable

from pydantic import BaseModel

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferData
from cg.store import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)
DDN = "DDN"
DEFAULT_SPRING_ARCHIVE_COUNT = 200

PathAndSample = namedtuple("PathAndSample", "path sample_internal_id")
ArchiveLocationAndSample = namedtuple("ArchiveLocationAndSample", "location sample_id")


class ArchiveModels(BaseModel):
    """Model containing the necessary file and sample information."""

    file_model: Callable
    archive_method: Callable


ARCHIVES_IN_USE: Dict[str, ArchiveModels] = {
    DDN: ArchiveModels(file_model=TransferData, archive_method=DDNDataFlowApi.archive_folders)
}


class ArchiveAPI:
    """Class handling the archiving of sample SPRING files."""

    def __init__(
        self, ddn_dataflow_api: DDNDataFlowApi, housekeeper_api: HousekeeperAPI, status_db: Store
    ):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.ddn_api: DDNDataFlowApi = ddn_dataflow_api
        self.status_db: Store = status_db

    def archive_samples(self, samples: List[Sample]) -> None:
        """Archives all non-archived spring files for the given samples."""
        files_to_archive: List[TransferData] = []
        for sample in samples:
            files_to_archive.extend(
                TransferData(destination=sample.internal_id, source=file.full_path)
                for file in self.housekeeper_api.get_non_archived_files(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                )
                if sample.archive_location == DDN
            )
        archive_task_id: int = self.ddn_api.archive_folders(
            sources_and_destinations=files_to_archive
        )
        self.housekeeper_api.add_archives(
            files=[Path(transfer_data.source) for transfer_data in files_to_archive],
            archive_task_id=archive_task_id,
        )

    def retrieve_sample(self, sample_ids: List[str]) -> None:
        """Archives all non-retrieved spring files for the given samples."""
        files_to_retrieve: List[TransferData] = []
        for sample_id in sample_ids:
            files_to_retrieve.extend(
                TransferData(destination=sample_id, source=file.as_posix())
                for file in self.housekeeper_api.get_non_archived_files(
                    bundle_name=sample_id, tags=[SequencingFileTag.SPRING]
                )
            )
        retrieve_task_id: int = self.ddn_api.retrieve_folders(
            sources_and_destinations=files_to_retrieve
        )
        self.housekeeper_api.add_retrieve_task(
            files=[Path(transfer_data.source) for transfer_data in files_to_retrieve],
            retrieve_task_id=retrieve_task_id,
        )

    def archive_all_non_archived_spring_files(
        self, spring_file_count_limit: int = DEFAULT_SPRING_ARCHIVE_COUNT
    ) -> None:
        """Archives all non archived spring files (so far only for DDN customers)."""

        files_archive: List[PathAndSample] = [
            PathAndSample(path=path, sample_internal_id=sample_id)
            for sample_id, path in self.housekeeper_api.get_non_archived_spring_path_and_bundle_name()[
                :spring_file_count_limit
            ]
        ]
        sorted_files_to_archive: Dict[
            str, List[PathAndSample]
        ] = self.sort_files_on_archive_location(files_archive)

        for archive_location in sorted_files_to_archive:
            if archive_location not in ARCHIVES_IN_USE:
                LOG.warning(f"No support for archiving using the location: {archive_location}")
                continue
            files_archive_info: List[TransferData] = [
                ARCHIVES_IN_USE[archive_location].file_model(
                    destination=file.sample_internal_id,
                    source=file.path,
                )
                for file in sorted_files_to_archive[archive_location]
            ]
            archive_task_id: int = ARCHIVES_IN_USE[archive_location].archive_method(
                self=self.ddn_api, sources_and_destinations=files_archive_info
            )

            self.housekeeper_api.add_archives(
                files=[Path(file.path) for file in sorted_files_to_archive[archive_location]],
                archive_task_id=archive_task_id,
            )

    def sort_files_on_archive_location(
        self,
        file_data: List[PathAndSample],
    ) -> Dict[str, List[PathAndSample]]:
        """Add the archive location to each file in the given list and return the list."""
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
