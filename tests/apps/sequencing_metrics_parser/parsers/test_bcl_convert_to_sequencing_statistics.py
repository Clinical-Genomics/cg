"""Test for the bcl_convert_to_sequencing_statistics parser."""
from pathlib import Path

from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import (
    BclConvertMetricsParser,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert_to_sequencing_statistics import (
    create_bcl_convert_undetermined_metrics,
    create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell,
)
from cg.store.models import SampleLaneSequencingMetrics


def test_create_sequencing_statistics_from_bcl_convert_metrics(
    bcl_convert_metrics_dir_path: Path,
    parsed_bcl_convert_metrics: BclConvertMetricsParser,
):
    """Test to create sequencing statistics from bcl convert metrics."""
    # GIVEN a parsed bcl convert metrics file

    # WHEN creating sequencing statistics from bcl convert metrics
    sequencing_statistics_list: list[
        SampleLaneSequencingMetrics
    ] = create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell(
        flow_cell_dir=bcl_convert_metrics_dir_path,
    )

    # THEN assert that Sequencing statistics are created
    for sequencing_statistics in sequencing_statistics_list:
        assert isinstance(sequencing_statistics, SampleLaneSequencingMetrics)

    # THEN assert that the number of sequencing statistics created is correct
    assert (
        len(sequencing_statistics_list)
        == len(parsed_bcl_convert_metrics.get_sample_internal_ids()) * 2
    )


def test_create_undetermined_sequencing_statistics_from_bcl_convert_metrics(
    bcl_convert_metrics_dir_path: Path,
):
    """Test creating undetermined sequencing statistics from bcl convert metrics."""

    # GIVEN a directory with a flow cell demultiplexed with bcl convert with undetermined reads

    # WHEN creating undetermined sequencing statistics from bcl convert metrics
    metrics: list[SampleLaneSequencingMetrics] = create_bcl_convert_undetermined_metrics(
        flow_cell_dir=bcl_convert_metrics_dir_path,
        non_pooled_lane_sample_pairs=[(1, "sample_id")],
    )

    # THEN metrics are created for the undetermined reads
    assert isinstance(metrics, list)
    assert isinstance(metrics[0], SampleLaneSequencingMetrics)


def test_create_undetermined_sequencing_statistics_from_bcl_convert_metrics_for_existing_lane_without_undetermined_reads(
    bcl_convert_metrics_dir_path: Path,
):
    """Test creating undetermined sequencing statistics from bcl convert metrics without undetermined reads."""

    # GIVEN a directory with a flow cell demultiplexed with bcl convert without undetermined reads in a lane

    # WHEN creating undetermined sequencing statistics from bcl convert metrics specifying an existing lane without undetermined reads
    metrics: list[SampleLaneSequencingMetrics] = create_bcl_convert_undetermined_metrics(
        flow_cell_dir=bcl_convert_metrics_dir_path,
        non_pooled_lane_sample_pairs=[(2, "sample_id")],
    )

    # THEN an empty list is returned
    assert not metrics
