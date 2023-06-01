"""Test for the bcl_convert_to_sequencing_statistics parser."""
from cg.store.models import SampleLaneSequencingMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert_to_sequencing_statistics import (
    create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell,
)
from pathlib import Path
from typing import List


def test_create_sequencing_statistics_from_bcl_convert_metrics(
    bcl_convert_metrics_dir_path: Path,
    parsed_bcl_convert_metrics: BclConvertMetricsParser,
):
    """Test to create sequencing statistics from bcl convert metrics."""
    # GIVEN a parsed bcl convert metrics file

    # WHEN creating sequencing statistics from bcl convert metrics
    sequencing_statistics_list: List[
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

    # THEN assert that the sequencing statistics are correct
