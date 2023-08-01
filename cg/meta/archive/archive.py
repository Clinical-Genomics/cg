import logging
from collections import namedtuple
from pathlib import Path
from typing import Dict, List, Optional, Callable

from housekeeper.store.models import File
from pydantic import ConfigDict
from pydantic import BaseModel

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.archiving import ArchiveLocationsInUse
from cg.meta.archive.ddn_dataflow import DDNDataFlowApi, DataFlowFileTransferData
from cg.meta.archive.models import ArchiveHandler, FileTransferData
from cg.store import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)
DEFAULT_SPRING_ARCHIVE_COUNT = 200

PathAndSample = namedtuple("PathAndSample", "path sample_internal_id")
ArchiveLocationAndSample = namedtuple("ArchiveLocationAndSample", "location sample_id")


class FileAndSample(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    file: File
    sample: Sample


class ArchiveModels(BaseModel):
    """Model containing the necessary file and sample information."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    file_model: Callable
    handler: ArchiveHandler


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
        self.handler_map: Dict[str, ArchiveModels] = {
            ArchiveLocationsInUse.KAROLINSKA_BUCKET: ArchiveModels(
                file_model=DataFlowFileTransferData.from_models, handler=self.ddn_api
            )
        }

    def archive_samples(self, samples: List[Sample]) -> None:
        """Archives all non-archived spring files for the given samples."""
        files_to_archive: List[DataFlowFileTransferData] = []
        for sample in samples:
            files_to_archive.extend(
                DataFlowFileTransferData(destination=sample.internal_id, source=file.full_path)
                for file in self.housekeeper_api.get_non_archived_files(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                )
                if sample.archive_location == "DDN"
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
        files_to_retrieve: List[DataFlowFileTransferData] = []
        for sample_id in sample_ids:
            files_to_retrieve.extend(
                DataFlowFileTransferData(destination=sample_id, source=file.as_posix())
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

        files_to_archive: List[File] = self.housekeeper_api.get_all_non_archived_spring_files()
        files_and_samples: List[FileAndSample] = self.add_samples_to_files(files_to_archive)

        for archive_location in ArchiveLocationsInUse:
            selected_files: [List[FileAndSample]] = get_files_by_archive_location(
                files_and_samples=files_and_samples, archive_location=archive_location
            )

            converted_files: List[FileTransferData] = self.convert_into_correct_model(
                files_and_samples=files_and_samples, archive_location=archive_location
            )

            archive_task_id: int = self.invoke_corresponding_archiving_function(
                files=converted_files, archive_location=archive_location
            )

            self.housekeeper_api.add_archives(
                files=[Path(file.path) for file in selected_files],
                archive_task_id=archive_task_id,
            )

    def invoke_corresponding_archiving_function(
        self, files: List[FileTransferData], archive_location: ArchiveLocationsInUse
    ) -> int:
        return self.handler_map[archive_location].handler.archive_folders(
            sources_and_destinations=files
        )

    def get_sample(self, file: PathAndSample) -> Optional[Sample]:
        sample: Optional[Sample] = self.status_db.get_sample_by_internal_id(file.sample_internal_id)
        if not sample:
            LOG.warning(
                f"No sample found in status_db corresponding to sample_id {file.sample_internal_id}."
                f"Skipping archiving for corresponding file {file.path}."
            )
        return sample

    def add_samples_to_files(self, files_to_archive: List[File]):
        files_and_samples = []
        for file in files_to_archive:
            sample: Optional[Sample] = self.get_sample(file)
            if sample:
                files_and_samples.append(FileAndSample(file=file, sample=sample))
        return files_and_samples

    def convert_into_correct_model(
        self, files_and_samples: List[FileAndSample], archive_location: ArchiveLocationsInUse
    ) -> List[FileTransferData]:
        return [
            self.handler_map[archive_location].file_model(
                file=file_and_sample.file, sample=file_and_sample.sample
            )
            for file_and_sample in files_and_samples
        ]
