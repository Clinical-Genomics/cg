"""Tests for the sequencing metrics parser API."""

from pathlib import Path

from cg.apps.sequencing_metrics_parser.api import (
    create_sample_lane_sequencing_metrics_for_flow_cell,
    create_undetermined_non_pooled_metrics,
)
from cg.apps.sequencing_metrics_parser.parser import MetricsParser
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.store.models import SampleLaneSequencingMetrics


def test_create_sample_lane_sequencing_metrics_for_flow_cell(
    bcl_convert_metrics_dir_path: Path,
    parsed_bcl_convert_metrics: MetricsParser,
):
    """Test to create sequencing statistics from bcl convert metrics."""
    # GIVEN a parsed bcl convert metrics file

    # WHEN creating sequencing statistics from bcl convert metrics
    sequencing_statistics_list: list[SampleLaneSequencingMetrics] = (
        create_sample_lane_sequencing_metrics_for_flow_cell(
            flow_cell_directory=bcl_convert_metrics_dir_path,
        )
    )

    # THEN assert that Sequencing statistics are created
    for sequencing_statistics in sequencing_statistics_list:
        assert isinstance(sequencing_statistics, SampleLaneSequencingMetrics)

    # THEN assert that the number of sequencing statistics created is correct
    assert (
        len(sequencing_statistics_list)
        == len(parsed_bcl_convert_metrics.get_sample_internal_ids()) * 2
    )


def test_create_undetermined_non_pooled_metrics(
    bcl_convert_flow_cell: FlowCellDirectoryData,
):
    """Test creating undetermined sequencing statistics from demultiplex metrics."""
    # GIVEN a directory with a demultiplexed flow cell with undetermined reads
    sample_sheet_path = Path(bcl_convert_flow_cell.path, "SampleSheet.csv")
    bcl_convert_flow_cell.set_sample_sheet_path_hk(hk_path=sample_sheet_path)

    # WHEN creating undetermined sequencing statistics from bcl convert metrics
    metrics: list[SampleLaneSequencingMetrics] = create_undetermined_non_pooled_metrics(
        flow_cell=bcl_convert_flow_cell
    )

    # THEN metrics are created for the undetermined reads
    assert isinstance(metrics, list)
    assert isinstance(metrics[0], SampleLaneSequencingMetrics)


def test_create_undetermined_non_pooled_metrics_for_existing_lane_without_undetermined_reads(
    bcl_convert_metrics_dir_path: Path,
):
    """
    Test creating undetermined sequencing statistics from demultiplex metrics without undetermined
    reads.
    """

    # GIVEN a directory with a demultiplexed flow cell without undetermined reads in a lane
    flow_cell = FlowCellDirectoryData(bcl_convert_metrics_dir_path)
    sample_sheet_path = Path(bcl_convert_metrics_dir_path, "SampleSheet.csv")
    flow_cell.set_sample_sheet_path_hk(hk_path=sample_sheet_path)

    # WHEN creating undetermined sequencing statistics specifying a lane without undetermined reads
    metrics: list[SampleLaneSequencingMetrics] = create_undetermined_non_pooled_metrics(
        flow_cell=flow_cell
    )

    # THEN an empty list is returned
    assert not metrics
