import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from attr import dataclass
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, TransferData
from cg.store import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)
DDN = "DDN"


class ArchiveAPI:
    """Class handling the archiving of sample SPRING files."""

    def __init__(
        self, ddn_dataflow_api: DDNDataFlowApi, housekeeper_api: HousekeeperAPI, status_db: Store
    ):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.ddn_api: DDNDataFlowApi = ddn_dataflow_api
        self.status_db: Store = status_db

    def archive_samples(self, sample_ids: List[str]) -> None:
        """Archives all non-archived spring files for the given samples."""
        samples_filtered_on_archive_location: Dict[
            str, List[str]
        ] = self.sample_ids_sorted_on_archive_location(sample_ids)
        files_to_archive: List[TransferData] = []
        # For future development; add support for other archive locations by looping through the dictionary.
        for sample_id in samples_filtered_on_archive_location[DDN]:
            files_to_archive.extend(
                TransferData(destination=sample_id, source=file.as_posix())
                for file in self.housekeeper_api.get_non_archived_files(
                    bundle_name=sample_id, tags=[SequencingFileTag.SPRING]
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

    def sample_ids_sorted_on_archive_location(self, sample_ids: List[str]) -> Dict[str, List[str]]:
        """Returns a dictionary with a data archive locations as key, and the subset of the given list of samples
        belonging to customers with said data archive location as value."""
        sample_ids_per_archive_location: Dict[str, List[str]] = {}
        for sample_id in sample_ids:
            data_archive_location: str = self.status_db.get_sample_by_internal_id(
                sample_id
            ).customer.data_archive_location
            if sample_ids_per_archive_location.get(data_archive_location):
                sample_ids_per_archive_location[data_archive_location].append(sample_id)
            else:
                sample_ids_per_archive_location[data_archive_location] = [sample_id]
        return sample_ids_per_archive_location

    def archive_all_non_archived_spring_files(self):
        spring_files_to_archive: List[
            str
        ] = self.housekeeper_api.get_all_non_archived_spring_files()
        if not spring_files_to_archive:
            LOG.info("Found no files ready to be archived.")
            return
        sample_and_spring_files_per_archive_location: Dict[
            str, List[Tuple[str, str]]
        ] = self.spring_files_sorted_on_archive_location(spring_files_to_archive)
        files_to_archive: List[TransferData] = [
            TransferData(destination=ddn_file_to_archive[0], source=ddn_file_to_archive[1])
            for ddn_file_to_archive in sample_and_spring_files_per_archive_location[DDN]
        ]
        archive_task_id: int = self.ddn_api.archive_folders(
            sources_and_destinations=files_to_archive
        )
        self.housekeeper_api.add_archives(
            files=[Path(transfer_data.source) for transfer_data in files_to_archive],
            archive_task_id=archive_task_id,
        )

    def spring_files_sorted_on_archive_location(
        self, files: List[str]
    ) -> Dict[str, List[Tuple[str, str]]]:
        files_per_archive_location: Dict[str, List[Tuple[str, str]]] = {}
        for file in files:
            (
                data_archive_location,
                sample_id,
            ) = self.get_archive_location_and_sample_id_from_file_path(file)
            if not data_archive_location:
                continue
            if files_per_archive_location.get(data_archive_location):
                files_per_archive_location[data_archive_location].append((sample_id, file))
            else:
                files_per_archive_location[data_archive_location] = [(sample_id, file)]
        return files_per_archive_location

    def get_archive_location_and_sample_id_from_file_path(
        self, file_path: str
    ) -> Optional[Tuple[str, str]]:
        sample_internal_id: str = self.get_sample_id_from_path(file_path)
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_internal_id)
        if not sample:
            LOG.warning(
                f"No sample found in status_db corresponding to sample_id {sample_internal_id}."
                f"Skipping archiving for corresponding file {file_path}."
            )
            return
        return sample.customer.data_archive_location, sample_internal_id

    def get_sample_id_from_path(self, file_path: str):
        return self.housekeeper_api.get_version_by_version_id(
            self.housekeeper_api.files(path=file_path).version_id
        ).bundle_id
