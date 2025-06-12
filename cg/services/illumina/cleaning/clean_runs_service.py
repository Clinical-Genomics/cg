"""Service to clean Illumina run directories."""

import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.time import TWENTY_ONE_DAYS
from cg.exc import (
    HousekeeperBundleVersionMissingError,
    HousekeeperFileMissingError,
    IlluminaCleanRunError,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.store.models import IlluminaSampleSequencingMetrics, IlluminaSequencingRun
from cg.store.store import Store
from cg.utils.files import remove_directory_and_contents
from cg.utils.time import is_directory_older_than_days_old

LOG = logging.getLogger(__name__)


class IlluminaCleanRunsService:
    """
    Handles the cleaning of Illumina runs in the sequencing-runs and demultiplexed-runs directories.
    Requirements for cleaning:
            Sequencing run is older than 21 days
            Sequencing run is backed up
            Sequencing run is in StatusDB
            Sequencing run has sequencing metrics in StatusDB
            Sequencing run has fastq files in Housekeeper or
                Sequencing run has SPRING files in Housekeeper
                and
                Sequencing run has SPRING metadata in Housekeeper
            Sequencing run has a sample sheet in Housekeeper
    """

    def __init__(
        self,
        status_db: Store,
        housekeeper_api: HousekeeperAPI,
        sequencing_run_path: Path,
        dry_run: bool,
    ):
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.sequencing_run_dir_data = IlluminaRunDirectoryData(
            sequencing_run_path=sequencing_run_path
        )
        self.dry_run: bool = dry_run
        LOG.info(f"Trying to delete {sequencing_run_path}")

    def delete_run_directory(self) -> None:
        """
        Delete the sequencing runs and demultiplexed runs directory if it fulfills all requirements.
        Raises:
            IlluminaCleanRunError when any exception is caught
        """
        try:
            self.set_sample_sheet_path_from_housekeeper()
            if self.can_run_directory_be_deleted():
                if self.dry_run:
                    LOG.debug(f"Dry run: Would have removed: {self.sequencing_run_dir_data.path}")
                    return
                remove_directory_and_contents(self.sequencing_run_dir_data.path)
        except Exception as error:
            raise IlluminaCleanRunError(
                f"Sequencing run with path {self.sequencing_run_dir_data.path} not removed: {repr(error)}"
            )

    def set_sample_sheet_path_from_housekeeper(self):
        """
        Set the sample sheet for a sequencing run.
        Raises:
            HousekeeperFileMissingError when the sample sheet is missing in Housekeeper
        """
        sample_sheet_path: Path = self.hk_api.get_sample_sheet_path(self.sequencing_run_dir_data.id)
        self.sequencing_run_dir_data.set_sample_sheet_path_hk(sample_sheet_path)

    def can_run_directory_be_deleted(self) -> bool:
        """Determine whether a sequencing run or demultiplexed run can be deleted."""
        return all(
            [
                self.is_directory_older_than_21_days(),
                self.is_sequencing_run_in_statusdb(),
                self.is_sequencing_run_backed_up(),
                self.has_sequencing_metrics_in_statusdb(),
                self.has_sample_fastq_or_spring_files_in_housekeeper(),
                self.has_sample_sheet_in_housekeeper(),
            ]
        )

    def is_directory_older_than_21_days(self) -> bool:
        """Check if a given directory is older than 21 days."""
        return is_directory_older_than_days_old(
            directory_path=self.sequencing_run_dir_data.path,
            days_old=TWENTY_ONE_DAYS,
        )

    def is_sequencing_run_in_statusdb(self) -> bool:
        """Check if sequencing run is in StatusDB."""
        return bool(self.get_sequencing_run_from_status_db())

    def is_sequencing_run_backed_up(self) -> bool:
        """Check if sequencing run is backed up on PDC."""
        return self.get_sequencing_run_from_status_db().has_backup

    def has_sequencing_metrics_in_statusdb(self) -> bool:
        """Check if a sequencing run has entries in the IlluminaSampleSequencingMetrics table."""
        return bool(self.get_sequencing_metrics_for_sequencing_run())

    def has_sample_sheet_in_housekeeper(self) -> bool:
        """Check if the sequencing run has a sample sheet in Housekeeper."""
        return bool(self.sequencing_run_dir_data.get_sample_sheet_path_hk())

    def has_fastq_files_for_samples_in_housekeeper(self) -> bool:
        """Check if all samples on the sequencing run have fastq files in Housekeeper."""
        return bool(self.get_files_for_samples_on_flow_cell_with_tag(tag=SequencingFileTag.FASTQ))

    def has_spring_files_for_samples_in_housekeeper(self) -> bool:
        """Check if all samples on the sequencing run have SPRING files in Housekeeper."""
        return bool(self.get_files_for_samples_on_flow_cell_with_tag(tag=SequencingFileTag.SPRING))

    def has_spring_meta_data_files_for_samples_in_housekeeper(self) -> bool:
        """Check if all samples on the sequencing run have SPRING metadata files in Housekeeper."""
        return bool(
            self.get_files_for_samples_on_flow_cell_with_tag(tag=SequencingFileTag.SPRING_METADATA)
        )

    def has_sample_fastq_or_spring_files_in_housekeeper(self) -> bool:
        """
        Check if a flow cell has fastq or spring files in Housekeeper.
        Raises:
            HousekeeperFileMissingError
        """
        if not self.has_fastq_files_for_samples_in_housekeeper() and not (
            self.has_spring_files_for_samples_in_housekeeper()
            and self.has_spring_meta_data_files_for_samples_in_housekeeper()
        ):
            raise HousekeeperFileMissingError(
                f"sequencing run {self.sequencing_run_dir_data.id} is missing fastq and spring files for some samples."
            )
        return True

    def get_sequencing_run_from_status_db(self) -> IlluminaSequencingRun | None:
        """
        Get the sequencing run entry from StatusDB.
        Raises:
            ValueError if the sequencing run is not found in StatusDB.
        """
        sequencing_run: IlluminaSequencingRun = (
            self.status_db.get_illumina_sequencing_run_by_device_internal_id(
                self.sequencing_run_dir_data.id
            )
        )
        return sequencing_run

    def get_sequencing_metrics_for_sequencing_run(
        self,
    ) -> list[IlluminaSampleSequencingMetrics] | None:
        """
        Get the sample sequencing metrics entries for a sequencing run.
        Raises:
              Value error if no IlluminaSampleSequencingMetrics are found in StatusDB.
        """
        sequencing_run: IlluminaSequencingRun = self.get_sequencing_run_from_status_db()
        metrics: list[IlluminaSampleSequencingMetrics] = sequencing_run.sample_metrics
        if not metrics:
            raise ValueError(
                f"No sample sequencing metrics found for {self.sequencing_run_dir_data.id} in StatusDB."
            )
        return metrics

    def get_files_for_samples_on_flow_cell_with_tag(self, tag: str) -> list[File] | None:
        """Return the files with the specified tag for all samples on a sequencing run."""
        sequencing_run: IlluminaSequencingRun = self.get_sequencing_run_from_status_db()
        bundle_names: list[str] = [
            metrics.sample.internal_id for metrics in sequencing_run.sample_metrics
        ]
        files: list[File] = []
        for bundle_name in bundle_names:
            try:
                files.extend(
                    self.hk_api.get_files_from_latest_version(
                        bundle_name=bundle_name, tags=[tag, self.sequencing_run_dir_data.id]
                    )
                )
            except HousekeeperBundleVersionMissingError:
                LOG.warning(
                    f"No files with tag {tag} found on flow cell {self.sequencing_run_dir_data.id}"
                )
                LOG.warning(f"Bundle: {bundle_name} not found in Housekeeper.")
                return None
        return files
