import logging
from collections import namedtuple
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferData
from cg.store import Store
from cg.store.models import Sample
from housekeeper.store.models import Version

LOG = logging.getLogger(__name__)
DDN = "DDN"

SampleAndFile = namedtuple("SampleAndFile", "sample file")
ArchiveLocationAndSample = namedtuple("ArchiveLocationAndSample", "location sample_id")


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
        samples_sorted_on_data_archive_location: Dict[
            str, List[Sample]
        ] = samples_sorted_on_archive_location(samples)
        files_to_archive: List[TransferData] = []
        # For future development; add support for other archive locations by looping through the dictionary.
        for sample in samples_sorted_on_data_archive_location[DDN]:
            files_to_archive.extend(
                TransferData(destination=sample.internal_id, source=file.full_path)
                for file in self.housekeeper_api.get_non_archived_files(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                )
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

    def archive_all_non_archived_spring_files(self) -> None:
        """Archives all non archived spring files (so far only for DDN customers)."""

        spring_files_to_archive: List[str] = [
            file.path for file in self.housekeeper_api.get_all_non_archived_spring_files()
        ]

        if not spring_files_to_archive:
            LOG.info("Found no files ready to be archived.")
            return

        sample_and_spring_files_per_archive_location: Dict[
            str, List[SampleAndFile]
        ] = self.sort_spring_files_on_archive_location(spring_files_to_archive)
        files_to_archive: List[TransferData] = [
            TransferData(destination=ddn_file_to_archive.sample, source=ddn_file_to_archive.file)
            for ddn_file_to_archive in sample_and_spring_files_per_archive_location[DDN]
        ]
        archive_task_id: int = self.ddn_api.archive_folders(
            sources_and_destinations=files_to_archive
        )
        self.housekeeper_api.add_archives(
            files=[Path(transfer_data.source) for transfer_data in files_to_archive],
            archive_task_id=archive_task_id,
        )

    def sort_spring_files_on_archive_location(
        self, files: List[str]
    ) -> Dict[str, List[SampleAndFile]]:
        """Sort the given list of files and gives back a dictionary
        mapping the data archive location to a tuple containing sample id and file path."""
        files_per_archive_location: Dict[str, List[SampleAndFile]] = {}
        for file in files:
            location_and_sample: ArchiveLocationAndSample = (
                self.get_archive_location_and_sample_id_from_file_path(file)
            )
            if not location_and_sample:
                continue
            archive_location: str = location_and_sample.location
            sample_id: str = location_and_sample.sample_id
            if files_per_archive_location.get(location_and_sample.location):
                files_per_archive_location[archive_location].append(SampleAndFile(sample_id, file))
            else:
                files_per_archive_location[archive_location] = [SampleAndFile(sample_id, file)]
        return files_per_archive_location

    def get_archive_location_and_sample_id_from_file_path(
        self, file_path: str
    ) -> Optional[ArchiveLocationAndSample]:
        """Returns the data archive location and sample id connected to the Housekeeper spring file."""
        sample_internal_id: str = self.get_sample_id_from_file_path(file_path)
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_internal_id)
        if not sample:
            LOG.warning(
                f"No sample found in status_db corresponding to sample_id {sample_internal_id}."
                f"Skipping archiving for corresponding file {file_path}."
            )
            return
        return ArchiveLocationAndSample(sample.customer.data_archive_location, sample_internal_id)

    def get_sample_id_from_file_path(self, file_path: str):
        """Return the sample id, i.e. bundle name, for the specified spring file in Housekeeper."""
        version: Version = self.housekeeper_api.get_version_by_version_id(
            self.housekeeper_api.files(path=file_path).first().version_id
        )
        return version.bundle_id
