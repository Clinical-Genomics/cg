"""Tests for the illumina clean runs service."""

import logging
import time

import mock
import pytest
from _pytest.logging import LogCaptureFixture
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.time import TWENTY_ONE_DAYS_IN_SECONDS
from cg.exc import IlluminaCleanRunError, HousekeeperFileMissingError
from cg.services.illumina.cleaning.clean_runs_service import (
    IlluminaCleanRunsService,
)
from cg.store.exc import EntryNotFoundError
from cg.store.models import (
    Sample,
    IlluminaSequencingRun,
    IlluminaSampleSequencingMetrics,
)
from tests.store_helpers import StoreHelpers


def test_get_sequencing_run_from_statusdb(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to get a sequencing run from statusdb."""

    # GIVEN an Illumina clean sequencing runs service with a store that contains a sequencing run

    # WHEN retrieving the sequencing run from the store
    sequencing_run: IlluminaSequencingRun = (
        illumina_clean_service_can_be_removed.get_sequencing_run_from_status_db()
    )

    # THEN a sequencing run is retrieved
    assert isinstance(sequencing_run, IlluminaSequencingRun)


def test_is_sequencing_run_in_statusdb(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to check that a sequencing run is in statusdb."""
    # GIVEN a clean illumina clean sequencing runs service with a store that contains a sequencing run

    # WHEN checking whether a sequencing run is in status DB
    is_in_statusdb: bool = illumina_clean_service_can_be_removed.is_sequencing_run_in_statusdb()

    # THEN checking whether a sequencing run is in statusdb is TRUE
    assert is_in_statusdb


def test_is_sequencing_run_backed_up(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to check that a sequencing run has been backed up."""
    # GIVEN a clean illumina clean sequencing runs service with a sequencing run that has been backed up

    # WHEN checking whether the sequencing run has been backed
    is_backed_up: bool = illumina_clean_service_can_be_removed.is_sequencing_run_backed_up()

    # THEN checking whether the sequencing run has been backed up is TRUE
    assert is_backed_up


def test_is_not_sequencing_run_backed_up(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to check that a sequencing run has been backed up."""
    # GIVEN a clean illumina clean sequencing runs service with a sequencing run that has not been backed up
    illumina_clean_service_can_be_removed.get_sequencing_run_from_status_db().has_backup = False

    # WHEN checking whether the sequencing run has been backed
    is_backed_up: bool = illumina_clean_service_can_be_removed.is_sequencing_run_backed_up()

    # THEN checking whether the sequencing run has been backed up is FALSE
    assert not is_backed_up


def test_get_sequencing_metrics_for_sequencing_run_from_statusdb(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to get a sequencing metrics for a sequencing run from statusdb."""

    # GIVEN a illumina clean sequencing runs service with a store that contains a sequencing run with IlluminaSampleSequencingMetrics entries

    # WHEN retrieving the sequencing run from the store
    metrics: list[IlluminaSampleSequencingMetrics] = (
        illumina_clean_service_can_be_removed.get_sequencing_metrics_for_sequencing_run()
    )

    # THEN a IlluminaSampleSequencingMetrics entry is retrieved
    assert isinstance(metrics[0], IlluminaSampleSequencingMetrics)


def test_has_sequencing_metrics_in_statusdb(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to check that a sequencing run has IlluminaSampleSequencingMetrics entries in statusdb."""

    # GIVEN an Illumina clean sequencing runs service with a store that contains a sequencing run with IlluminaSampleSequencingMetrics entries

    # WHEN THEN checking whether a sequencing run has IlluminaSampleSequencingMetrics entries'
    has_metrics: bool = illumina_clean_service_can_be_removed.has_sequencing_metrics_in_statusdb()

    # THEN checking whether a sequencing run has IlluminaSampleSequencingMetrics entries returns True
    assert has_metrics


def test_is_directory_older_than_21_days_pass(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN an Illumina clean sequencing runs service with a sequencing run that can be deleted

    # WHEN checking whether a given sequencing run directory is older than 21 days

    with mock.patch(
        "time.time",
        return_value=time.time() + TWENTY_ONE_DAYS_IN_SECONDS,
    ):
        is_older_that_21_days: bool = (
            illumina_clean_service_can_be_removed.is_directory_older_than_21_days()
        )

    # THEN checking whether a given sequencing run directory is older than 21 days is TRUE
    assert is_older_that_21_days


def test_is_directory_older_than_21_days_fail(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN an Illumina clean sequencing runs service with a current time that is set to now.

    # WHEN checking whether a given sequencing run directory is older than 21 days
    is_older_than_21_days: bool = (
        illumina_clean_service_can_be_removed.is_directory_older_than_21_days()
    )

    # THEN checking whether a given sequencing run directory is older than 21 days is FALSE
    assert not is_older_than_21_days


def test_has_sample_sheet_in_housekeeper(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test to check whether a sequencing run has a sample sheet in housekeeper."""

    # GIVEN an Illumina clean sequencing runs service with a sequencing run that has a sample sheet in housekeeper

    # WHEN checking whether the sequencing run has a sample sheet in housekeeper
    has_sample_sheet: bool = illumina_clean_service_can_be_removed.has_sample_sheet_in_housekeeper()

    # THEN checking whether the sequencing run has a sample sheet in housekeeper returns TRUE
    assert has_sample_sheet


@pytest.mark.parametrize(
    "tag",
    [SequencingFileTag.FASTQ, SequencingFileTag.SPRING, SequencingFileTag.SPRING_METADATA],
    ids=["fastq", "spring", "spring_metadata"],
)
def test_get_files_for_flow_cell_bundle(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService, tag: str
):
    """Test to get files for a sequencing run bundle from housekeeper."""

    # GIVEN an Illumina clean sequencing runs service with a sequencing run that has files in housekeeper

    # WHEN getting the sequencing run samples' files
    files: list[File] = (
        illumina_clean_service_can_be_removed.get_files_for_samples_on_flow_cell_with_tag(tag=tag)
    )

    # THEN files are returned
    assert files


@pytest.mark.parametrize(
    "tag",
    [SequencingFileTag.FASTQ, SequencingFileTag.SPRING, SequencingFileTag.SPRING_METADATA],
    ids=["fastq", "spring", "spring_metadata"],
)
def test_get_files_for_samples_on_flow_cell_with_tag_missing_sample(
    illumina_clean_service_can_not_be_removed: IlluminaCleanRunsService,
    helpers: StoreHelpers,
    tag: str,
    selected_novaseq_6000_pre_1_5_kits_sample_ids: list[str],
    caplog: LogCaptureFixture,
):
    """Test that a sequencing run is cleaned if one of its samples is missing in Housekeeper."""
    caplog.set_level(logging.WARNING)

    # GIVEN a store with a sequencing run to be cleaned

    # GIVEN that the sequencing run has two samples
    first_sample: Sample = (
        illumina_clean_service_can_not_be_removed.status_db.get_sample_by_internal_id(
            selected_novaseq_6000_pre_1_5_kits_sample_ids[0]
        )
    )
    second_sample: Sample = (
        illumina_clean_service_can_not_be_removed.status_db.get_sample_by_internal_id(
            selected_novaseq_6000_pre_1_5_kits_sample_ids[1]
        )
    )
    assert first_sample
    assert second_sample

    # GIVEN that one of the samples is not in Housekeeper
    hk_api: HousekeeperAPI = illumina_clean_service_can_not_be_removed.hk_api
    assert not hk_api.bundle(second_sample.internal_id)

    # WHEN getting the sequencing run samples' files
    files: list[File] = (
        illumina_clean_service_can_not_be_removed.get_files_for_samples_on_flow_cell_with_tag(
            tag=tag
        )
    )

    # THEN files are returned
    assert not files

    # THEN a warning is logged
    assert f"Bundle: {first_sample.internal_id} not found in Housekeeper" in caplog.text


def test_can_sequencing_run_be_deleted(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test the sequencing run can be deleted check."""
    # GIVEN a sequencing run that can be deleted

    with mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.is_directory_older_than_21_days",
        return_value=True,
    ):
        # WHEN checking that the sequencing run can be deleted
        can_be_deleted: bool = illumina_clean_service_can_be_removed.can_run_directory_be_deleted()

    # THEN the check whether the sequencing run can be deleted returns True
    assert can_be_deleted


def test_can_sequencing_run_be_deleted_no_spring_with_fastq(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test that a sequencing run can be deleted when it has fastq files but no spring files."""
    # GIVEN a sequencing run that can be deleted

    with mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.is_directory_older_than_21_days",
        return_value=True,
    ):
        with mock.patch(
            "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.has_spring_meta_data_files_for_samples_in_housekeeper",
            return_value=False,
        ):
            # WHEN checking that the sequencing run can be deleted
            can_be_deleted: bool = (
                illumina_clean_service_can_be_removed.can_run_directory_be_deleted()
            )

    # THEN the check whether the sequencing run can be deleted returns True
    assert can_be_deleted


def test_can_sequencing_run_be_deleted_spring_no_fastq(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test that a sequencing run can be deleted when it has spring files but no fastq files."""
    # GIVEN a sequencing run that can be deleted

    with mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.is_directory_older_than_21_days",
        return_value=True,
    ):
        with mock.patch(
            "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.has_fastq_files_for_samples_in_housekeeper",
            return_value=False,
        ):
            # WHEN checking that the sequencing run can be deleted
            can_be_deleted: bool = (
                illumina_clean_service_can_be_removed.can_run_directory_be_deleted()
            )

    # THEN the check whether the sequencing run can be deleted returns True
    assert can_be_deleted


def test_can_sequencing_run_be_deleted_no_spring_no_fastq(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test that a sequencing run can not be deleted when it has no spring files and no fastq files."""
    # GIVEN a sequencing run that can be deleted
    with mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.is_directory_older_than_21_days",
        return_value=True,
    ), mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.has_fastq_files_for_samples_in_housekeeper",
        return_value=False,
    ), mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.has_spring_meta_data_files_for_samples_in_housekeeper",
        return_value=False,
    ):
        # WHEN checking that the sequencing run can be deleted

        # THEN a HousekeeperFileMissingError is raised
        with pytest.raises(HousekeeperFileMissingError):
            illumina_clean_service_can_be_removed.can_run_directory_be_deleted()


def test_delete_sequencing_run_directory(
    illumina_clean_service_can_be_removed: IlluminaCleanRunsService,
):
    """Test that a sequencing run directory is removed."""
    # GIVEN a sequencing run that can be removed

    # GIVEN that the sequencing run directory exists
    assert illumina_clean_service_can_be_removed.sequencing_run_dir_data.path.exists()

    # WHEN removing the sequencing run directory
    with mock.patch(
        "cg.services.illumina.cleaning.clean_runs_service.IlluminaCleanRunsService.is_directory_older_than_21_days",
        return_value=True,
    ):
        illumina_clean_service_can_be_removed.delete_run_directory()

    # THEN the sequencing run directory is removed
    assert not illumina_clean_service_can_be_removed.sequencing_run_dir_data.path.exists()


def test_delete_sequencing_run_directory_can_not_be_deleted(
    illumina_clean_service_can_not_be_removed: IlluminaCleanRunsService,
):
    """Test delete a sequencing run that does not pass all checks."""
    # GIVEN a sequencing run that should not be removed.

    # GIVEN that the sequencing run directory exists
    assert illumina_clean_service_can_not_be_removed.sequencing_run_dir_data.path.exists()

    # WHEN trying to remove the sequencing run
    with pytest.raises(IlluminaCleanRunError):
        illumina_clean_service_can_not_be_removed.delete_run_directory()

    # THEN the sequencing run directory still exists
    illumina_clean_service_can_not_be_removed.sequencing_run_dir_data.path.exists()


def test_get_sequencing_run_from_statusdb_does_not_exist(
    illumina_clean_service_can_not_be_removed: IlluminaCleanRunsService,
):
    """Test retrieving a sequencing run from statusDB that does not exist."""
    # GIVEN a illumina clean sequencing runs service with a sequencing run that is not in statusDB
    illumina_clean_service_can_not_be_removed.sequencing_run_dir_data.id = (
        "flow_cell_does_not_exist"
    )

    # WHEN retrieving the sequencing run from statusDB

    # THEN a ValueError is raised
    with pytest.raises(EntryNotFoundError):
        illumina_clean_service_can_not_be_removed.get_sequencing_run_from_status_db()


def test_sequencing_run_has_not_fastq_files_in_housekeeper(
    illumina_clean_service_can_not_be_removed: IlluminaCleanRunsService,
    caplog,
):
    """Test to check wether a sequencing run has files in Housekeeper."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sequencing run that has entries in StatusDB but does not have any files in Housekeeper for its samples

    # WHEN checking whether a sample on a sequencing run has fastq files

    # THEN the sequencing run has no fastq files in housekeeper.
    assert (
        not illumina_clean_service_can_not_be_removed.has_fastq_files_for_samples_in_housekeeper()
    )
    assert SequencingFileTag.FASTQ in caplog.text


def test_sequencing_run_has_not_spring_files_in_housekeeper(
    illumina_clean_service_can_not_be_removed: IlluminaCleanRunsService,
    caplog,
):
    """Test to check whether a sequencing run has files in Housekeeper."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sequencing run that has entries in StatusDB but does not have any files in Housekeeper for its samples

    # WHEN checking whether a sample on a sequencing run has spring files

    # THEN the sequencing run has no spring files for samples in housekeeper
    assert (
        not illumina_clean_service_can_not_be_removed.has_spring_files_for_samples_in_housekeeper()
    )
    assert SequencingFileTag.SPRING in caplog.text


def test_sequencing_run_has_not_spring_meta_data_files_in_housekeeper(
    illumina_clean_service_can_not_be_removed: IlluminaCleanRunsService,
    caplog,
):
    """Test to check whether a sequencing run has files in Housekeeper."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sequencing run that has entries in StatusDB but does not have any files in Housekeeper for its samples

    # WHEN checking whether a sample on a sequencing run has spring files

    # THEN the sequencing run has no spring metadata files in housekeeper

    assert (
        not illumina_clean_service_can_not_be_removed.has_spring_meta_data_files_for_samples_in_housekeeper()
    )
    assert SequencingFileTag.SPRING_METADATA in caplog.text


def test_has_no_sample_files_in_housekeeper(
    illumina_clean_service_can_not_be_removed: IlluminaCleanRunsService,
):
    # GIVEN a sequencing run that has entries in StatusDB but does not have any files in Housekeeper for its samples

    # WHEN checking whether a sample on a sequencing run has files in housekeeper

    # THEN a HousekeeperFileMissingError is raised
    with pytest.raises(HousekeeperFileMissingError):
        illumina_clean_service_can_not_be_removed.has_sample_fastq_or_spring_files_in_housekeeper()
