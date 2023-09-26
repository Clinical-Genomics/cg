"""Tests for the clean flow cells API."""
import time
from typing import List

from housekeeper.store.models import File

from cg.constants import SequencingFileTag
from cg.meta.clean.clean_flow_cells import CleanFlowCellAPI
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
    assert flow_cell_clean_api_can_be_removed.has_sequencing_metrics()


def test_is_directory_older_than_days_old_pass(
    flow_cell_clean_api_can_be_removed: CleanFlowCellAPI,
):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN a clean flow cell api with a current time that is set 21 days from now

    # THEN checking whether a given flow cell directory is older than 21 days is TRUE
    assert flow_cell_clean_api_can_be_removed.is_directory_older_than_days_old()


def test_is_directory_not_than_days_old_fail(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check whether a directory is older than 21 days."""

    # GIVEN a clean flow cell api with a current time that is set to now.
    flow_cell_clean_api_can_be_removed.current_time = time.time()

    # THEN checking whether a given flow cell directory is older than 21 days is FALSE
    assert not flow_cell_clean_api_can_be_removed.is_directory_older_than_days_old()


def test_has_sample_sheet_in_housekeeper(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to check whether a flow cell has a sample sheet in housekeeper."""

    # GIVEN a clean flow cell api with a flow cell that has a sample sheet in housekeeper

    # THEN checking whether the flow cell has a sample sheet in housekeeper returns TRUE
    assert flow_cell_clean_api_can_be_removed.has_sample_sheet_in_housekeeper()


def test_get_files_for_flow_cell_bundle(flow_cell_clean_api_can_be_removed: CleanFlowCellAPI):
    """Test to get files for a flow cell bundle from housekeeper."""

    # GIVEN a clean flow cell api with a flow cell that has files in housekeeper

    # WHEN getting fastq and spring files that are tagged with the flow cell
    fastq_files: List[File] = flow_cell_clean_api_can_be_removed.get_files_for_flow_cell_bundle(
        tag=SequencingFileTag.FASTQ
    )
    spring_files: List[File] = flow_cell_clean_api_can_be_removed.get_files_for_flow_cell_bundle(
        tag=SequencingFileTag.SPRING
    )

    # THEN fastq and SPRING files are returned
    assert fastq_files
    assert spring_files
