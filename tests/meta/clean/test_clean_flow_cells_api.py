"""Tests for the clean flow cells API."""
import time
from typing import List

import pytest
from housekeeper.store.models import File

from cg.constants import SequencingFileTag
from cg.exc import HousekeeperBundleVersionMissingError
from cg.meta.clean.clean_flow_cells import CleanFlowCellAPI
from cg.store import Store
from cg.store.models import Flowcell, SampleLaneSequencingMetrics


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

    # THEN checking whether a flow cell is in statusdb is TRUE
    assert flow_cell_clean_api_can_be_removed.is_flow_cell_in_statusdb()


def test_is_flow_cell_backed_up(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check that a flow cell has been backed up."""
    # GIVEN a clean flow cell api with a flow cell that has been backed up

    # THEN checking whether the flow cell has been backed up is TRUE
    assert flow_cell_clean_api_can_be_removed.is_flow_cell_backed_up()


def test_is_not_flow_cell_backed_up(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check that a flow cell has been backed up."""
    # GIVEN a clean flow cell api with a flow cell that has not been backed up
    flow_cell_clean_api_can_be_removed.get_flow_cell_from_status_db().has_backup = False

    # THEN checking whether the flow cell has been backed up is TRUE
    assert not flow_cell_clean_api_can_be_removed.is_flow_cell_backed_up()


def test_get_sequencing_metrics_for_flow_cell_from_statusdb(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test to get a sequencing metrics for a flow cell from statusdb."""

    # GIVEN a clean flow cell api with a store that contains a flow cell with SampleLaneSequencingMetrics entries

    # WHEN retrieving the flow cell from the store
    metrics: List[
        SampleLaneSequencingMetrics
    ] = flow_cell_clean_api_can_be_removed.get_sequencing_metrics_for_flow_cell()

    # THEN a flow cell is retrieved
    assert isinstance(metrics[0], SampleLaneSequencingMetrics)


def test_has_sequencing_metrics_in_statusdb(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check that a flow cell has SampleLaneSequencingMetrics entries in statusdb."""

    # GIVEN a clean flow cell api with a store that contains a flow cell with SampleLaneSequencingMetrics entries

    # THEN checking whether a flow cell has SampleLaneSequencingMetrics entries returns True
    assert flow_cell_clean_api_can_be_removed.has_sequencing_metrics_in_statusdb()


def test_is_directory_older_than_days_old_pass(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN a clean flow cell api with a current time that is set 21 days from now

    # THEN checking whether a given flow cell directory is older than 21 days is TRUE
    assert flow_cell_clean_api_can_be_removed.is_directory_older_than_21_days()


def test_is_directory_not_than_days_old_fail(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN a clean flow cell api with a current time that is set to now.
    flow_cell_clean_api_can_be_removed.current_time = time.time()

    # THEN checking whether a given flow cell directory is older than 21 days is FALSE
    assert not flow_cell_clean_api_can_be_removed.is_directory_older_than_21_days()


def test_has_sample_sheet_in_housekeeper(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check whether a flow cell has a sample sheet in housekeeper."""

    # GIVEN a clean flow cell api with a flow cell that has a sample sheet in housekeeper

    # THEN checking whether the flow cell has a sample sheet in housekeeper returns TRUE
    assert flow_cell_clean_api_can_be_removed.has_sample_sheet_in_housekeeper()


def test_get_files_for_flow_cell_bundle(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to get files for a flow cell bundle from housekeeper."""

    # GIVEN a clean flow cell api with a flow cell that has files in housekeeper

    # WHEN getting fastq and spring files that are tagged with the flow cell
    fastq_files: List[
        File
    ] = flow_cell_clean_api_can_be_removed.has_files_for_samples_on_flow_cell_with_tag(
        tag=SequencingFileTag.FASTQ
    )
    spring_files: List[
        File
    ] = flow_cell_clean_api_can_be_removed.has_files_for_samples_on_flow_cell_with_tag(
        tag=SequencingFileTag.SPRING
    )
    spring_metadata_files: List[
        File
    ] = flow_cell_clean_api_can_be_removed.has_files_for_samples_on_flow_cell_with_tag(
        tag=SequencingFileTag.SPRING_METADATA
    )

    # THEN fastq and SPRING files are returned
    assert fastq_files
    assert spring_files
    assert spring_metadata_files


def test_can_flow_cell_be_deleted(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test the flow cell can be deleted check."""
    # GIVEN a flow cell that can be deleted

    # WHEN checking that the flow cell can be deleted

    # THEN the check whether the flow cell can be deleted returns True
    assert flow_cell_clean_api_can_be_removed.can_flow_cell_directory_be_deleted()


def test_delete_flow_cell_directory(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test that a flow cell directory is removed."""
    # GIVEN a flow cell that cen be removed

    # GIVEN that the flow cell directory exists
    assert flow_cell_clean_api_can_be_removed.flow_cell.path.exists()

    # WHEN removing the flow cell directory
    error_is_raised: bool = flow_cell_clean_api_can_be_removed.delete_flow_cell_directory()

    # THEN the flow cell directory is removed
    assert not flow_cell_clean_api_can_be_removed.flow_cell.path.exists()

    # THEN a bool is returned that no error is raised
    assert not error_is_raised


def test_delete_flow_cell_directory_can_not_be_deleted(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI,
):
    """Test delete a flow cell that does not pass all checks."""
    # GIVEN a flow cell that should not be removed.

    # GIVEN that the flow cell directory exists
    assert flow_cell_clean_api_can_not_be_removed.flow_cell.path.exists()

    # WHEN trying to remove the flow cell
    error_raised: bool = flow_cell_clean_api_can_not_be_removed.delete_flow_cell_directory()

    # THEN the flow cell directory still exists
    flow_cell_clean_api_can_not_be_removed.flow_cell.path.exists()

    # THEN a bool is returned whether an error has been raised
    assert error_raised


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
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI, store_with_flow_cell_to_clean: Store
):
    """Test to check wether a flow cell has files in Housekeeper."""
    # GIVEN a flow cell that has entries in StatusDB but does not have any files in Housekeeper for its samples
    flow_cell_clean_api_can_not_be_removed.status_db = store_with_flow_cell_to_clean

    # WHEN checking whether a sample on a flow cell has fastq files

    # THEN a HousekeeperBundleVersionMissingError is raised
    with pytest.raises(HousekeeperBundleVersionMissingError):
        flow_cell_clean_api_can_not_be_removed.has_fastq_files_for_samples_in_housekeeper()


def test_flow_cell_has_not_spring_files_in_housekeeper(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI, store_with_flow_cell_to_clean: Store
):
    """Test to check whether a flow cell has files in Housekeeper."""
    # GIVEN a flow cell that has entries in StatusDB but does not have any files in Housekeeper for its samples
    flow_cell_clean_api_can_not_be_removed.status_db = store_with_flow_cell_to_clean

    # WHEN checking whether a sample on a flow cell has spring files

    # THEN a HousekeeperBundleVersionMissingError is raised
    with pytest.raises(HousekeeperBundleVersionMissingError):
        flow_cell_clean_api_can_not_be_removed.has_spring_files_for_samples_in_housekeeper()


def test_flow_cell_has_not_spring_meta_data_files_in_housekeeper(
    flow_cell_clean_api_can_not_be_removed: CleanFlowCellAPI, store_with_flow_cell_to_clean: Store
):
    """Test to check whether a flow cell has files in Housekeeper."""
    # GIVEN a flow cell that has entries in StatusDB but does not have any files in Housekeeper for its samples
    flow_cell_clean_api_can_not_be_removed.status_db = store_with_flow_cell_to_clean

    # WHEN checking whether a sample on a flow cell has spring files

    # THEN a HousekeeperBundleVersionMissingError is raised
    with pytest.raises(HousekeeperBundleVersionMissingError):
        flow_cell_clean_api_can_not_be_removed.has_spring_meta_data_files_for_samples_in_housekeeper()
