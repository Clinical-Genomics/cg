import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.archiving import ArchiveLocations
from cg.meta.archive.ddn_dataflow import DDNDataFlowClient
from cg.meta.archive.models import ArchiveHandler, FileAndSample, SampleAndHousekeeperDestination
from cg.models.cg_config import DataFlowConfig
from cg.store import Store
from cg.store.models import Flowcell, Sample
from housekeeper.store.models import File
from pydantic import BaseModel, ConfigDict

LOG = logging.getLogger(__name__)
DEFAULT_SPRING_ARCHIVE_COUNT = 200


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


def filter_samples_on_archive_location(
    samples_and_housekeeper_destinations: List[SampleAndHousekeeperDestination],
    archive_location: ArchiveLocations,
) -> List[SampleAndHousekeeperDestination]:
    """
    Returns a list of FileAndSample where the associated sample has a specific archive location.
    """
    return [
        sample_and_housekeeper_destination
        for sample_and_housekeeper_destination in samples_and_housekeeper_destinations
        if sample_and_housekeeper_destination.sample.archive_location == archive_location
    ]


ARCHIVE_HANDLERS: Dict[str, Type[ArchiveHandler]] = {
    ArchiveLocations.KAROLINSKA_BUCKET: DDNDataFlowClient
}


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
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[archive_location](self.data_flow_config)
        return archive_handler.archive_files(files_and_samples=files)

    def archive_archive_location(
        self, files_and_samples: List[FileAndSample], archive_location: ArchiveLocations
    ) -> None:
        """Archives a collection of files in the specified location and adds corresponding entries in HouseKeeper."""
        selected_files: [List[FileAndSample]] = filter_files_on_archive_location(
            files_and_samples=files_and_samples, archive_location=archive_location
        )
        archive_task_id: int = self.archive_files(
            files=selected_files, archive_location=archive_location
        )
        self.housekeeper_api.add_archives(
            files=[Path(file_and_sample.file.path) for file_and_sample in selected_files],
            archive_task_id=archive_task_id,
        )

    def archive_all_non_archived_spring_files(
        self, spring_file_count_limit: int = DEFAULT_SPRING_ARCHIVE_COUNT
    ) -> None:
        """Archives all non archived spring files."""

        files_to_archive: List[File] = self.housekeeper_api.get_all_non_archived_spring_files()[
            :spring_file_count_limit
        ]
        files_and_samples: List[FileAndSample] = self.add_samples_to_files(files_to_archive)

        for archive_location in ArchiveLocations:
            self.archive_archive_location(
                files_and_samples=files_and_samples,
                archive_location=archive_location,
            )

    def retrieve_flowcell(self, flowcell_name: str) -> None:
        """Retrieves the archived spring files for all samples ran on the specified flowcell."""
        flowcell: Flowcell = self.status_db.get_flow_cell_by_name(flowcell_name)
        samples_to_fetch: List[SampleAndHousekeeperDestination] = self.get_samples_to_retrieve(
            flowcell
        )
        for archive_location in ArchiveLocations:
            filtered_samples: List[
                SampleAndHousekeeperDestination
            ] = filter_samples_on_archive_location(
                samples_and_housekeeper_destinations=samples_to_fetch,
                archive_location=archive_location,
            )
            if filtered_samples:
                job_id: int = self.retrieve_samples_from_archive_location(
                    samples_and_destinations=filtered_samples,
                    archive_location=archive_location,
                )
                self.set_archive_retrieval_task_ids(
                    retrieval_task_id=job_id,
                    files=self.get_spring_files_from_samples(
                        [sample.sample for sample in filtered_samples]
                    ),
                )

    def get_spring_files_from_samples(self, samples: List[Sample]) -> List[File]:
        """Gets all spring files in Housekeeper in the bundles corresponding to the given list of samples."""
        files: List[File] = []
        for sample in samples:
            files.extend(
                self.housekeeper_api.get_files_from_latest_version(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                ).all()
            )
        return files

    def get_samples_to_retrieve(self, flowcell: Flowcell) -> List[SampleAndHousekeeperDestination]:
        """Gets all samples which were run on the specified flowcell and clumps it with the destination in
        Housekeeper where we want the retrieved files to be."""
        samples_to_retrieve: List[SampleAndHousekeeperDestination] = []
        for sample in flowcell.samples:
            LOG.info(f"Will try to retrieve sample: {sample.internal_id}.")
            housekeeper_destination: str = self.get_destination_from_sample_internal_id(
                sample.internal_id
            )
            samples_to_retrieve.append(
                SampleAndHousekeeperDestination(
                    sample=sample, housekeeper_destination=housekeeper_destination
                )
            )
        return samples_to_retrieve

    def retrieve_samples_from_archive_location(
        self,
        samples_and_destinations: List[SampleAndHousekeeperDestination],
        archive_location: ArchiveLocations,
    ):
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[archive_location](self.data_flow_config)
        return archive_handler.retrieve_samples(samples_and_destinations)

    def retrieve_sample(self, sample_internal_id: str) -> None:
        """Retrieves all archived spring files for the given sample."""
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_internal_id)
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[sample.archive_location](
            self.data_flow_config
        )
        housekeeper_destination: str = self.get_destination_from_sample_internal_id(
            sample_internal_id
        )
        retrieval_task_id: int = archive_handler.retrieve_samples(
            [
                SampleAndHousekeeperDestination(
                    sample=sample, housekeeper_destination=housekeeper_destination
                )
            ]
        )
        spring_files: List[File] = self.housekeeper_api.get_archived_files(
            bundle_name=sample_internal_id, tags=[SequencingFileTag.SPRING]
        )
        self.set_archive_retrieval_task_ids(retrieval_task_id=retrieval_task_id, files=spring_files)

    def get_destination_from_sample_internal_id(self, sample_internal_id):
        """Returns where in Housekeeper to put the retrieved spring files for the specified sample."""
        return self.housekeeper_api.get_latest_bundle_version(
            sample_internal_id
        ).full_path.as_posix()

    def set_archive_retrieval_task_ids(self, retrieval_task_id: int, files: List[File]):
        for file in files:
            self.housekeeper_api.set_archive_retrieval_task_id(
                file_id=file.id, retrieval_task_id=retrieval_task_id
            )

    def retrieve_spring_file(self, file_path: str):
        """Retrieves the archived spring file."""
        file: File = self.housekeeper_api.files(path=file_path).first()
        sample: Sample = self.status_db.get_sample_by_internal_id(file.version.bundle.name)
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[sample.archive_location](
            self.data_flow_config
        )
        retrieval_task_id: int = archive_handler.retrieve_file(
            FileAndSample(file=file, sample=sample)
        )
        self.housekeeper_api.set_archive_retrieval_task_id(
            file_id=file.id, retrieval_task_id=retrieval_task_id
        )

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
