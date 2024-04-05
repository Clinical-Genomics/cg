"""Tests for the clean flow cells API."""

import logging
import time

import mock
import pytest
from _pytest.logging import LogCaptureFixture
from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.time import TWENTY_ONE_DAYS_IN_SECONDS
from cg.exc import CleanFlowCellFailedError, HousekeeperFileMissingError
from cg.meta.clean.clean_flow_cells import CleanFlowCellAPI
from cg.store.models import Flowcell, Sample, SampleLaneSequencingMetrics
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_flow_cell_from_statusdb(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to get a flow cell from statusdb."""

    # GIVEN a clean flow cell api with a store that contains a flow cell

    # WHEN retrieving the flow cell from the store
    flow_cell: Flowcell = flow_cell_clean_api_can_be_removed.get_flow_cell_from_status_db()

    # THEN a flow cell is retrieved
    assert isinstance(flow_cell, Flowcell)


def test_is_flow_cell_in_statusdb(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check that a flow cell is in statusdb."""
    # GIVEN a clean flow cell api with a store that contains a flow cell

    # WHEN checking whether a flow cell is in status DB
    is_in_statusdb: bool = flow_cell_clean_api_can_be_removed.is_flow_cell_in_statusdb()

    # THEN checking whether a flow cell is in statusdb is TRUE
    assert is_in_statusdb


def test_is_flow_cell_backed_up(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check that a flow cell has been backed up."""
    # GIVEN a clean flow cell api with a flow cell that has been backed up

    # WHEN checking whether the flow cell has been backed
    is_backed_up: bool = flow_cell_clean_api_can_be_removed.is_flow_cell_backed_up()

    # THEN checking whether the flow cell has been backed up is TRUE
    assert is_backed_up


def test_is_not_flow_cell_backed_up(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check that a flow cell has been backed up."""
    # GIVEN a clean flow cell api with a flow cell that has not been backed up
    flow_cell_clean_api_can_be_removed.get_flow_cell_from_status_db().has_backup = False

    # WHEN checking whether the flow cell has been backed
    is_backed_up: bool = flow_cell_clean_api_can_be_removed.is_flow_cell_backed_up()

    # THEN checking whether the flow cell has been backed up is FALSE
    assert not is_backed_up


def test_get_sequencing_metrics_for_flow_cell_from_statusdb(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test to get a sequencing metrics for a flow cell from statusdb."""

    # GIVEN a clean flow cell api with a store that contains a flow cell with SampleLaneSequencingMetrics entries

    # WHEN retrieving the flow cell from the store
    metrics: list[SampleLaneSequencingMetrics] = (
        flow_cell_clean_api_can_be_removed.get_sequencing_metrics_for_flow_cell()
    )

    # THEN a SampleLaneSequencingMetrics entry is retrieved
    assert isinstance(metrics[0], SampleLaneSequencingMetrics)


def test_has_sequencing_metrics_in_statusdb(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check that a flow cell has SampleLaneSequencingMetrics entries in statusdb."""

    # GIVEN a clean flow cell api with a store that contains a flow cell with SampleLaneSequencingMetrics entries

    # WHEN THEN checking whether a flow cell has SampleLaneSequencingMetrics entries'
    has_metrics: bool = flow_cell_clean_api_can_be_removed.has_sequencing_metrics_in_statusdb()

    # THEN checking whether a flow cell has SampleLaneSequencingMetrics entries returns True
    assert has_metrics


def test_is_directory_older_than_21_days_pass(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN a clean flow cell api with a flow cell that can be deleted

    # WHEN checking whether a given flow cell directory is older than 21 days

    with mock.patch(
        "time.time",
        return_value=time.time() + TWENTY_ONE_DAYS_IN_SECONDS,
    ):
        is_older_that_21_days: bool = (
            flow_cell_clean_api_can_be_removed.is_directory_older_than_21_days()
        )

    # THEN checking whether a given flow cell directory is older than 21 days is TRUE
    assert is_older_that_21_days


def test_is_directory_older_than_21_days_fail(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN a clean flow cell api with a current time that is set to now.

    # WHEN checking whether a given flow cell directory is older than 21 days
    is_older_than_21_days: bool = (
        flow_cell_clean_api_can_be_removed.is_directory_older_than_21_days()
    )

    # THEN checking whether a given flow cell directory is older than 21 days is FALSE
    assert not is_older_than_21_days


def test_has_sample_sheet_in_housekeeper(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check whether a flow cell has a sample sheet in housekeeper."""

    # GIVEN a clean flow cell api with a flow cell that has a sample sheet in housekeeper

    # WHEN checking whether the flow cell has a sample sheet in housekeeper
    has_sample_sheet: bool = flow_cell_clean_api_can_be_removed.has_sample_sheet_in_housekeeper()

    # THEN checking whether the flow cell has a sample sheet in housekeeper returns TRUE
    assert has_sample_sheet


@pytest.mark.parametrize(
    "tag",
    [SequencingFileTag.FASTQ, SequencingFileTag.SPRING, SequencingFileTag.SPRING_METADATA],
    ids=["fastq", "spring", "spring_metadata"],
)
def test_get_files_for_flow_cell_bundle(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI, tag: str
):
    """Test to get files for a flow cell bundle from housekeeper."""

    # GIVEN a clean flow cell api with a flow cell that has files in housekeeper

    # WHEN getting the flow cell samples' files
    files: list[File] = (
        flow_cell_clean_api_can_be_removed.get_files_for_samples_on_flow_cell_with_tag(tag=tag)
    )

    # THEN files are returned
    assert files


@pytest.mark.parametrize(
    "tag",
    [SequencingFileTag.FASTQ, SequencingFileTag.SPRING, SequencingFileTag.SPRING_METADATA],
    ids=["fastq", "spring", "spring_metadata"],
)
def test_get_files_for_samples_on_flow_cell_with_tag_missing_sample(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
    helpers: StoreHelpers,
    tag: str,
    caplog: LogCaptureFixture,
):
    """Test that a flow cell is cleaned if one of its samples is missing in Housekeeper."""
    caplog.set_level(logging.WARNING)

    # GIVEN a store with a flow cell to be cleaned
    store: Store = flow_cell_clean_api_can_be_removed.status_db
    flow_cell: Flowcell = flow_cell_clean_api_can_be_removed.get_flow_cell_from_status_db()

    # GIVEN that the flow cell has two samples
    sample: Sample = helpers.add_sample(
        store=store, customer_id="cust500", internal_id="123", name="123", flowcell=flow_cell
    )
    assert len(flow_cell.samples) == 2
    store.session.add(flow_cell)
    store.session.commit()

    # GIVEN that one of the samples is not in Housekeeper
    hk_api: HousekeeperAPI = flow_cell_clean_api_can_be_removed.hk_api
    assert not hk_api.bundle(sample.internal_id)

    # WHEN getting the flow cell samples' files
    files: list[File] = (
        flow_cell_clean_api_can_be_removed.get_files_for_samples_on_flow_cell_with_tag(tag=tag)
    )

    # THEN files are returned
    assert files

    # THEN a warning is logged
    assert f"Bundle: {sample.internal_id} not found in Housekeeper" in caplog.text


def test_can_flow_cell_be_deleted(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test the flow cell can be deleted check."""
    # GIVEN a flow cell that can be deleted

    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        # WHEN checking that the flow cell can be deleted
        can_be_deleted: bool = (
            flow_cell_clean_api_can_be_removed.can_flow_cell_directory_be_deleted()
        )

    # THEN the check whether the flow cell can be deleted returns True
    assert can_be_deleted


def test_can_flow_cell_be_deleted_no_spring_with_fastq(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test that a flow cell can be deleted when it has fastq files but no spring files."""
    # GIVEN a flow cell that can be deleted

    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        with mock.patch(
            "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.has_spring_meta_data_files_for_samples_in_housekeeper",
            return_value=False,
        ):
            # WHEN checking that the flow cell can be deleted
            can_be_deleted: bool = (
                flow_cell_clean_api_can_be_removed.can_flow_cell_directory_be_deleted()
            )

    # THEN the check whether the flow cell can be deleted returns True
    assert can_be_deleted


def test_can_flow_cell_be_deleted_spring_no_fastq(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test that a flow cell can be deleted when it has spring files but no fastq files."""
    # GIVEN a flow cell that can be deleted

    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        with mock.patch(
            "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.has_fastq_files_for_samples_in_housekeeper",
            return_value=False,
        ):
            # WHEN checking that the flow cell can be deleted
            can_be_deleted: bool = (
                flow_cell_clean_api_can_be_removed.can_flow_cell_directory_be_deleted()
            )

    # THEN the check whether the flow cell can be deleted returns True
    assert can_be_deleted


def test_can_flow_cell_be_deleted_no_spring_no_fastq(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test that a flow cell can not be deleted when it has no spring files and no fastq files."""
    # GIVEN a flow cell that can be deleted

    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        with mock.patch(
            "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.has_fastq_files_for_samples_in_housekeeper",
            return_value=False,
        ):
            with mock.patch(
                "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.has_spring_meta_data_files_for_samples_in_housekeeper",
                return_value=False,
            ):
                # WHEN checking that the flow cell can be deleted

                # THEN a HousekeeperFileMissingError is raised
                with pytest.raises(HousekeeperFileMissingError):
                    flow_cell_clean_api_can_be_removed.can_flow_cell_directory_be_deleted()


def test_delete_flow_cell_directory(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test that a flow cell directory is removed."""
    # GIVEN a flow cell that can be removed

    # GIVEN that the flow cell directory exists
    assert flow_cell_clean_api_can_be_removed.flow_cell.path.exists()

    # WHEN removing the flow cell directory
    with mock.patch(
        "cg.meta.clean.clean_flow_cells.CleanFlowCellAPI.is_directory_older_than_21_days",
        return_value=True,
    ):
        flow_cell_clean_api_can_be_removed.delete_flow_cell_directory()

    # THEN the flow cell directory is removed
    assert not flow_cell_clean_api_can_be_removed.flow_cell.path.exists()


def test_delete_flow_cell_directory_can_not_be_deleted(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI,
):
    """Test delete a flow cell that does not pass all checks."""
    # GIVEN a flow cell that should not be removed.

    # GIVEN that the flow cell directory exists
    assert flow_cell_clean_api_can_not_be_removed.flow_cell.path.exists()

    # WHEN trying to remove the flow cell
    with pytest.raises(CleanFlowCellFailedError):
        flow_cell_clean_api_can_not_be_removed.delete_flow_cell_directory()

    # THEN the flow cell directory still exists
    flow_cell_clean_api_can_not_be_removed.flow_cell.path.exists()


def test_get_flow_cell_from_statusdb_does_not_exist(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI,
):
    """Test retrieving a flow cell from statusDB that does not exist."""
    # GIVEN a CleanFlowCellAPI with a flow cell that is not in statusDB
    flow_cell_clean_api_can_not_be_removed.flow_cell.id = "flow_cell_does_not_exist"

    assert not flow_cell_clean_api_can_not_be_removed.status_db.get_flow_cell_by_name(
        flow_cell_clean_api_can_not_be_removed.flow_cell.id
    )

    # WHEN retrieving the flow cell from statusDB

    # THEN a ValueError is raised
    with pytest.raises(ValueError):
        flow_cell_clean_api_can_not_be_removed.get_flow_cell_from_status_db()


def test_flow_cell_has_not_fastq_files_in_housekeeper(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI,
    store_with_flow_cell_not_to_clean: Store,
    housekeeper_api_with_flow_cell_not_to_clean: HousekeeperAPI,
    caplog,
):
    """Test to check wether a flow cell has files in Housekeeper."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a flow cell that has entries in StatusDB but does not have any files in Housekeeper for its samples
    flow_cell_clean_api_can_not_be_removed.status_db = store_with_flow_cell_not_to_clean
    flow_cell_clean_api_can_not_be_removed.hk_api = housekeeper_api_with_flow_cell_not_to_clean

    # WHEN checking whether a sample on a flow cell has fastq files

    # THEN the flow cell has no fastq files in housekeeper.
    assert not flow_cell_clean_api_can_not_be_removed.has_fastq_files_for_samples_in_housekeeper()
    assert SequencingFileTag.FASTQ in caplog.text


def test_flow_cell_has_not_spring_files_in_housekeeper(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI,
    store_with_flow_cell_not_to_clean: Store,
    housekeeper_api_with_flow_cell_not_to_clean: HousekeeperAPI,
    caplog,
):
    """Test to check whether a flow cell has files in Housekeeper."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a flow cell that has entries in StatusDB but does not have any files in Housekeeper for its samples
    flow_cell_clean_api_can_not_be_removed.status_db = store_with_flow_cell_not_to_clean
    flow_cell_clean_api_can_not_be_removed.hk_api = housekeeper_api_with_flow_cell_not_to_clean

    # WHEN checking whether a sample on a flow cell has spring files

    # THEN the flow cell has no spring files for samples in housekeeper
    assert not flow_cell_clean_api_can_not_be_removed.has_spring_files_for_samples_in_housekeeper()
    assert SequencingFileTag.SPRING in caplog.text


def test_flow_cell_has_not_spring_meta_data_files_in_housekeeper(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI,
    store_with_flow_cell_not_to_clean: Store,
    housekeeper_api_with_flow_cell_not_to_clean: HousekeeperAPI,
    caplog,
):
    """Test to check whether a flow cell has files in Housekeeper."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a flow cell that has entries in StatusDB but does not have any files in Housekeeper for its samples
    flow_cell_clean_api_can_not_be_removed.status_db = store_with_flow_cell_not_to_clean
    flow_cell_clean_api_can_not_be_removed.hk_api = housekeeper_api_with_flow_cell_not_to_clean

    # WHEN checking whether a sample on a flow cell has spring files

    # THEN the flow cell has no spring metadata files in housekeeper

    assert (
        not flow_cell_clean_api_can_not_be_removed.has_spring_meta_data_files_for_samples_in_housekeeper()
    )
    assert SequencingFileTag.SPRING_METADATA in caplog.text


def test_has_no_sample_files_in_housekeeper(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI,
    store_with_flow_cell_not_to_clean: Store,
    housekeeper_api_with_flow_cell_not_to_clean: HousekeeperAPI,
):
    # GIVEN a flow cell that has entries in StatusDB but does not have any files in Housekeeper for its samples
    flow_cell_clean_api_can_not_be_removed.status_db = store_with_flow_cell_not_to_clean
    flow_cell_clean_api_can_not_be_removed.hk_api = housekeeper_api_with_flow_cell_not_to_clean

    # WHEN checking whether a sample on a flow cell has files in housekeeper

    # THEN a HousekeeperFileMissingError is raised
    with pytest.raises(HousekeeperFileMissingError):
        flow_cell_clean_api_can_not_be_removed.has_sample_fastq_or_spring_files_in_housekeeper()
