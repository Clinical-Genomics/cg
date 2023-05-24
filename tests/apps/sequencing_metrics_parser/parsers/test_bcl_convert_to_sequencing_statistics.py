"""Test for the bcl_convert_to_sequencing_statistics parser."""
from cg.store.models import SequencingStatistics
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert_to_sequencing_statistics import (
    create_sequencing_statistics_from_bcl_convert_metrics,
)
from pathlib import Path
from typing import List


def test_create_sequencing_statistics_from_bcl_convert_metrics(
    bcl_convert_demux_metric_file_path: Path,
    bcl_convert_quality_metric_file_path: Path,
    bcl_convert_sample_sheet_file_path: Path,
    bcl_convert_adapter_metrics_file_path: Path,
    bcl_convert_run_info_file_path: Path,
    parsed_bcl_convert_metrics: BclConvertMetricsParser,
):
    """Test to create sequencing statistics from bcl convert metrics."""
    # GIVEN a parsed bcl convert metrics file

    # WHEN creating sequencing statistics from bcl convert metrics
    sequencing_statistics_list: List[
        SequencingStatistics
    ] = create_sequencing_statistics_from_bcl_convert_metrics(
        adapter_metrics_file_path=bcl_convert_adapter_metrics_file_path,
        quality_metrics_file_path=bcl_convert_quality_metric_file_path,
        demux_metrics_file_path=bcl_convert_demux_metric_file_path,
        sample_sheet_file_path=bcl_convert_sample_sheet_file_path,
        run_info_file_path=bcl_convert_run_info_file_path,
    )

    # THEN assert that Sequencing statistics are created
    for sequencing_statistics in sequencing_statistics_list:
        assert isinstance(sequencing_statistics, SequencingStatistics)

    # THEN assert that the number of sequencing statistics created is correct
    assert (
        len(sequencing_statistics_list)
        == len(parsed_bcl_convert_metrics.get_sample_internal_ids()) * 2
    )

    # THEN assert that the sequencing statistics are correct
