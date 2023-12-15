import logging
from typing import Callable, Type

import click
from housekeeper.store.models import Archive, File
from pydantic import BaseModel, ConfigDict

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.archiving import ArchiveLocations
from cg.exc import ArchiveJobFailedError
from cg.meta.archive.ddn.ddn_data_flow_client import DDNDataFlowClient
from cg.meta.archive.models import ArchiveHandler, FileAndSample, SampleAndDestination
from cg.models.cg_config import DataFlowConfig
from cg.store import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)
ARCHIVE_HANDLERS: dict[str, Type[ArchiveHandler]] = {
    ArchiveLocations.KAROLINSKA_BUCKET: DDNDataFlowClient
}


class ArchiveModels(BaseModel):
    """Model containing the necessary file and sample information."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    file_model: Callable
    handler: ArchiveHandler


def filter_samples_on_archive_location(
    samples_and_destinations: list[SampleAndDestination],
    archive_location: ArchiveLocations,
) -> list[SampleAndDestination]:
    """
    Returns a list of SampleAndHousekeeperDestinations where the associated sample has a specific archive location.
    """
    return [
        sample_and_destination
        for sample_and_destination in samples_and_destinations
        if sample_and_destination.sample.archive_location == archive_location
    ]


class SpringArchiveAPI:
    """Class handling the archiving of sample SPRING files to an off-premise location for long
    term storage."""

    def __init__(
        self, housekeeper_api: HousekeeperAPI, status_db: Store, data_flow_config: DataFlowConfig
    ):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.status_db: Store = status_db
        self.data_flow_config: DataFlowConfig = data_flow_config

    def archive_files_to_location(
        self, files_and_samples: list[FileAndSample], archive_location: ArchiveLocations
    ) -> int:
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[archive_location](self.data_flow_config)
        return archive_handler.archive_files(files_and_samples=files_and_samples)

    def archive_spring_files_and_add_archives_to_housekeeper(
        self, spring_file_count_limit: int | None
    ) -> None:
        """Archives all non-archived spring files. If a limit is provided, the amount of files archived is limited
        to that amount."""
        if isinstance(spring_file_count_limit, int) and spring_file_count_limit <= 0:
            LOG.warning("Please do not provide a non-positive integer as limit - exiting.")
            return
        for archive_location in ArchiveLocations:
            files_to_archive: list[File] = self.housekeeper_api.get_non_archived_spring_files(
                tags=[archive_location],
                limit=spring_file_count_limit,
            )
            if files_to_archive:
                files_and_samples_for_location = self.add_samples_to_files(files_to_archive)
                job_id = self.archive_files_to_location(
                    files_and_samples=files_and_samples_for_location,
                    archive_location=archive_location,
                )
                LOG.info(f"Files submitted to {archive_location} with archival task id {job_id}.")
                self.housekeeper_api.add_archives(
                    files=[
                        file_and_sample.file for file_and_sample in files_and_samples_for_location
                    ],
                    archive_task_id=job_id,
                )
            else:
                LOG.info(f"No files to archive for location {archive_location}.")

    def retrieve_samples(self, sample_internal_ids: list[str]) -> None:
        """Retrieves the archived spring files for a list of samples."""
        samples: list[Sample] = [
            self.status_db.get_sample_by_internal_id(sample_internal_id)
            for sample_internal_id in sample_internal_ids
        ]
        samples_and_destinations: list[SampleAndDestination] = self.join_destinations_and_samples(
            samples
        )
        for archive_location in ArchiveLocations:
            filtered_samples: list[SampleAndDestination] = filter_samples_on_archive_location(
                samples_and_destinations=samples_and_destinations,
                archive_location=archive_location,
            )
            if filtered_samples:
                job_id: int = self.retrieve_samples_from_archive_location(
                    samples_and_destinations=filtered_samples,
                    archive_location=archive_location,
                )
                self.set_archive_retrieval_task_ids(
                    retrieval_task_id=job_id,
                    files=self.get_archived_files_from_samples(
                        [sample.sample for sample in filtered_samples]
                    ),
                )

    def get_archived_files_from_samples(self, samples: list[Sample]) -> list[File]:
        """Gets archived spring files from the bundles corresponding to the given list of samples."""
        files: list[File] = []
        for sample in samples:
            files.extend(
                self.housekeeper_api.get_archived_files_for_bundle(
                    bundle_name=sample.internal_id, tags=[SequencingFileTag.SPRING]
                )
            )
        return files

    def join_destinations_and_samples(self, samples: list[Sample]) -> list[SampleAndDestination]:
        """Gets all samples and combines them with their desired destination in Housekeeper."""
        samples_to_retrieve: list[SampleAndDestination] = []
        for sample in samples:
            LOG.debug(f"Will try to retrieve sample: {sample.internal_id}.")
            destination: str = self.get_destination_from_sample_internal_id(sample.internal_id)
            samples_to_retrieve.append(SampleAndDestination(sample=sample, destination=destination))
        return samples_to_retrieve

    def retrieve_samples_from_archive_location(
        self,
        samples_and_destinations: list[SampleAndDestination],
        archive_location: ArchiveLocations,
    ):
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[archive_location](self.data_flow_config)
        return archive_handler.retrieve_samples(samples_and_destinations)

    def get_destination_from_sample_internal_id(self, sample_internal_id) -> str:
        """Returns where in Housekeeper to put the retrieved spring files for the specified sample."""
        return self.housekeeper_api.get_latest_bundle_version(
            sample_internal_id
        ).full_path.as_posix()

    def set_archive_retrieval_task_ids(self, retrieval_task_id: int, files: list[File]) -> None:
        for file in files:
            self.housekeeper_api.set_archive_retrieval_task_id(
                file_id=file.id, retrieval_task_id=retrieval_task_id
            )

    def get_sample(self, file: File) -> Sample | None:
        """Fetches the Sample corresponding to a File and logs if a Sample is not found."""
        sample: Sample | None = self.status_db.get_sample_by_internal_id(file.version.bundle.name)
        if not sample:
            LOG.warning(
                f"No sample found in status_db corresponding to sample_id {file.version.bundle.name}."
                f"Skipping archiving for corresponding file {file.path}."
            )
        return sample

    def add_samples_to_files(self, files: list[File]) -> list[FileAndSample]:
        """Fetches the Sample corresponding to each File, instantiates a FileAndSample object and
        adds it to the list which is returned."""
        files_and_samples: list[FileAndSample] = []
        for file in files:
            if sample := self.get_sample(file):
                files_and_samples.append(FileAndSample(file=file, sample=sample))
        return files_and_samples

    def update_statuses_for_ongoing_tasks(self) -> None:
        """Updates any completed jobs with a finished timestamp."""
        self.update_ongoing_archivals()
        self.update_ongoing_retrievals()

    def update_ongoing_archivals(self) -> None:
        ongoing_archivals: list[Archive] = self.housekeeper_api.get_ongoing_archivals()
        archival_ids_per_location: dict[
            ArchiveLocations, list[int]
        ] = self.sort_archival_ids_on_archive_location(ongoing_archivals)
        for archive_location in ArchiveLocations:
            self.update_archival_jobs_for_archive_location(
                archive_location=archive_location,
                job_ids=archival_ids_per_location.get(archive_location),
            )

    def update_ongoing_retrievals(self) -> None:
        ongoing_retrievals: list[Archive] = self.housekeeper_api.get_ongoing_retrievals()
        retrieval_ids_per_location: dict[
            ArchiveLocations, list[int]
        ] = self.sort_retrieval_ids_on_archive_location(ongoing_retrievals)
        for archive_location in ArchiveLocations:
            self.update_retrieval_jobs_for_archive_location(
                archive_location=archive_location,
                job_ids=retrieval_ids_per_location.get(archive_location),
            )

    def update_archival_jobs_for_archive_location(
        self, archive_location: ArchiveLocations, job_ids: list[int]
    ) -> None:
        for job_id in job_ids:
            self.update_ongoing_task(
                task_id=job_id, archive_location=archive_location, is_archival=True
            )

    def update_retrieval_jobs_for_archive_location(
        self, archive_location: ArchiveLocations, job_ids: list[int]
    ) -> None:
        for job_id in job_ids:
            self.update_ongoing_task(
                task_id=job_id, archive_location=archive_location, is_archival=False
            )

    def update_ongoing_task(
        self, task_id: int, archive_location: ArchiveLocations, is_archival: bool
    ) -> None:
        """Fetches info on an ongoing job and updates the Archive entry in Housekeeper."""
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[archive_location](self.data_flow_config)
        try:
            LOG.info(f"Fetching status for job with id {task_id} from {archive_location}")
            is_job_done: bool = archive_handler.is_job_done(task_id)
            if is_job_done:
                LOG.info(f"Job with id {task_id} has finished, updating Archive entries.")
                if is_archival:
                    self.housekeeper_api.set_archived_at(task_id)
                else:
                    self.housekeeper_api.set_retrieved_at(task_id)
            else:
                LOG.info(f"Job with id {task_id} has not yet finished.")
        except ArchiveJobFailedError as error:
            LOG.error(error)
            if is_archival:
                LOG.warning(f"Will remove archive entries with archival task ids {task_id}")
                self.housekeeper_api.delete_archives(task_id)
            else:
                LOG.warning("Will set retrieval task id to null.")
                self.housekeeper_api.update_archive_retrieved_at(
                    old_retrieval_job_id=task_id, new_retrieval_job_id=None
                )

    def sort_archival_ids_on_archive_location(
        self, archive_entries: list[Archive]
    ) -> dict[ArchiveLocations, list[int]]:
        """Returns a dictionary with keys being ArchiveLocations and the values being the subset of the given
        archival jobs which should be archived there."""

        jobs_per_location: dict[ArchiveLocations, list[int]] = {}
        jobs_and_locations: set[
            tuple[int, ArchiveLocations]
        ] = self.get_unique_archival_ids_and_archive_locations(archive_entries)

        for archive_location in ArchiveLocations:
            jobs_per_location[ArchiveLocations(archive_location)] = [
                job_and_location[0]
                for job_and_location in jobs_and_locations
                if job_and_location[1] == archive_location
            ]
        return jobs_per_location

    def get_unique_archival_ids_and_archive_locations(
        self, archive_entries: list[Archive]
    ) -> set[tuple[int, ArchiveLocations]]:
        ids_and_locations: set[tuple[int, ArchiveLocations]] = set()
        for archive in archive_entries:
            if location := self.get_archive_location_from_file(archive.file):
                ids_and_locations.add((archive.archiving_task_id, location))
        return ids_and_locations

    def sort_retrieval_ids_on_archive_location(
        self, archive_entries: list[Archive]
    ) -> dict[ArchiveLocations, list[int]]:
        """Returns a dictionary with keys being ArchiveLocations and the values being the subset of the given
        retrieval jobs which should be archived there."""
        jobs_per_location: dict[ArchiveLocations, list[int]] = {}
        jobs_and_locations: set[
            tuple[int, ArchiveLocations]
        ] = self.get_unique_retrieval_ids_and_archive_locations(archive_entries)
        for archive_location in ArchiveLocations:
            jobs_per_location[ArchiveLocations(archive_location)] = [
                job_and_location[0]
                for job_and_location in jobs_and_locations
                if job_and_location[1] == archive_location
            ]
        return jobs_per_location

    def get_unique_retrieval_ids_and_archive_locations(
        self, archive_entries: list[Archive]
    ) -> set[tuple[int, ArchiveLocations]]:
        ids_and_locations: set[tuple[int, ArchiveLocations]] = set()
        for archive in archive_entries:
            if location := self.get_archive_location_from_file(archive.file):
                ids_and_locations.add((archive.retrieval_task_id, location))
        return ids_and_locations

    @staticmethod
    def is_file_archived(file: File) -> bool:
        return file.archive and file.archive.archived_at

    @staticmethod
    def get_archive_location_from_file(file: File) -> ArchiveLocations | None:
        for tag_name in [tag.name for tag in file.tags]:
            if tag_name in iter(ArchiveLocations):
                LOG.info(f"Found archive location {tag_name}")
                return tag_name
        LOG.warning("No archive location in the file tags")
        return None

    def delete_file_from_archive_location(
        self, file_and_sample: FileAndSample, archive_location: ArchiveLocations
    ) -> None:
        archive_handler: ArchiveHandler = ARCHIVE_HANDLERS[archive_location](self.data_flow_config)
        archive_handler.delete_file(file_and_sample)

    def delete_file(self, file_path: str, dry_run: bool = False) -> None:
        """Deletes the specified file where it is archived and deletes the Housekeeper record.
        Raises:
            Click.Abort if yes is not specified or the user does not confirm the deletion."""
        file: File = self.housekeeper_api.files(path=file_path).first()
        if not self.is_file_archived(file):
            LOG.warning(f"No archived file found for file {file_path} - exiting")
            return
        archive_location: ArchiveLocations | None = self.get_archive_location_from_file(file)
        if not archive_location:
            LOG.warning("No archive location could be determined - exiting")
            return
        if dry_run:
            click.echo(f"Would have deleted file {file_path} from {archive_location}.")
            return
        file_and_sample: FileAndSample = self.add_samples_to_files([file])[0]
        self.delete_file_from_archive_location(
            file_and_sample=file_and_sample, archive_location=archive_location
        )
        self.housekeeper_api.delete_file(file.id)
