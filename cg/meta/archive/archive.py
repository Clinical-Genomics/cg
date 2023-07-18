import logging
from collections import namedtuple
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferData
from cg.store import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)
DDN = "DDN"
DEFAULT_SPRING_ARCHIVE_COUNT = 200

SampleAndFile = namedtuple("SampleAndFile", "sample file")
ArchiveLocationAndSample = namedtuple("ArchiveLocationAndSample", "location sample_id")


class FileData(BaseModel):
    """Model containing the necessary file and sample information."""

    file: str
    sample_internal_id: str
    archive_location: Optional[str] = None


def samples_sorted_on_archive_location(samples: List[Sample]) -> Dict[str, List[Sample]]:
    """Returns a dictionary with a data archive locations as key, and the subset of the given list of samples
    belonging to customers with said data archive location as value."""
    samples_per_archive_location: Dict[str, List[Sample]] = {}
    for sample in samples:
        data_archive_location: str = sample.customer.data_archive_location
        if samples_per_archive_location.get(data_archive_location):
            samples_per_archive_location[data_archive_location].append(sample)
        else:
            samples_per_archive_location[data_archive_location] = [sample]
    return samples_per_archive_location


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

        spring_files_to_archive: List[FileData] = [
            FileData(file=file, sample_internal_id=sample)
            for sample, file in self.housekeeper_api.get_non_archived_spring_path_and_bundle_name()[
                :spring_file_count_limit
            ]
        ]

        if not spring_files_to_archive:
            LOG.info("Found no files ready to be archived.")
            return

        spring_files_with_location = self.add_archive_location_to_files(spring_files_to_archive)

        files_to_archive: List[TransferData] = [
            TransferData(
                destination=file_to_archive.sample_internal_id, source=file_to_archive.file
            )
            for file_to_archive in spring_files_with_location
            if file_to_archive.archive_location == DDN
        ]

        archive_task_id: int = self.ddn_api.archive_folders(
            sources_and_destinations=files_to_archive
        )

        self.housekeeper_api.add_archives(
            files=[Path(transfer_data.source) for transfer_data in files_to_archive],
            archive_task_id=archive_task_id,
        )

    def add_archive_location_to_files(
        self,
        samples_and_files: List[FileData],
    ) -> List[FileData]:
        """Add the archive location to each file in the given list and return the list."""
        for sample_and_file in samples_and_files:
            sample = self.status_db.get_sample_by_internal_id(sample_and_file.sample_internal_id)
            if not sample:
                LOG.warning(
                    f"No sample found in status_db corresponding to sample_id {sample_and_file.sample_internal_id}."
                    f"Skipping archiving for corresponding file {sample_and_file.file}."
                )
                continue
            sample_and_file.archive_location = sample.archive_location
        return samples_and_files
