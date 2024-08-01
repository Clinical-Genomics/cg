"""This module contains tests for the BCLConvert metrics parser."""

from pathlib import Path

import pytest

from cg.services.illumina.file_parsing.models import (
    SequencingQualityMetrics,
    DemuxMetrics,
)
from cg.services.illumina.file_parsing.bcl_convert_metrics_parser import (
    BCLConvertMetricsParser,
)


def test_parse_metrics(
    bcl_convert_metrics_dir_path: Path,
):
    """Test to parse BCLConvert metrics."""
    # GIVEN paths to a BCLConvert metrics files
    # WHEN parsing the files
    bcl_convert_metrics_parser = BCLConvertMetricsParser(
        bcl_convert_metrics_dir_path=bcl_convert_metrics_dir_path
    )

    # THEN assert that the metrics are parsed
    assert bcl_convert_metrics_parser.quality_metrics
    assert isinstance(bcl_convert_metrics_parser.quality_metrics[0], SequencingQualityMetrics)
    assert bcl_convert_metrics_parser.demux_metrics
    assert isinstance(bcl_convert_metrics_parser.demux_metrics[0], DemuxMetrics)


def test_parse_metrics_files_not_existing():
    """Test to parse BCLConvert metrics with non-existing path."""
    # GIVEN paths to a BCLConvert metrics files that do not exist
    # WHEN parsing the files assert that a FileNotFoundError is raised
    with pytest.raises(FileNotFoundError):
        BCLConvertMetricsParser(bcl_convert_metrics_dir_path=Path("non-existing-path"))


def test_parse_quality_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    bcl_convert_quality_metric_model_with_data: SequencingQualityMetrics,
):
    """Test to parse BCLConvert quality metrics."""
    # GIVEN a parsed BCLConvert metrics

    # ASSERT that the parsed quality metrics are correct
    quality_metrics_model: SequencingQualityMetrics = parsed_bcl_convert_metrics.quality_metrics[0]

    # ASSERT that the parsed quality metrics are of the correct type
    assert isinstance(quality_metrics_model, SequencingQualityMetrics)

    # ASSERT that the parsed quality metrics has the correct values
    for attr_name, attr_value in quality_metrics_model.model_dump().items():
        assert getattr(bcl_convert_quality_metric_model_with_data, attr_name) == attr_value


def test_parse_demux_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    bcl_convert_demux_metric_model_with_data: DemuxMetrics,
):
    """Test to parse BCLConvert demux metrics."""
    # GIVEN a parsed BCLConvert metrics

    # ASSERT that the parsed demux metrics are correct
    demux_metrics_model: DemuxMetrics = parsed_bcl_convert_metrics.demux_metrics[0]

    # ASSERT that the parsed demux metrics are of the correct type
    assert isinstance(demux_metrics_model, DemuxMetrics)

    # ASSERT that the parsed demux metrics has the correct values
    for attr_name, attr_value in demux_metrics_model.model_dump().items():
        assert getattr(bcl_convert_demux_metric_model_with_data, attr_name) == attr_value


def test_get_sample_internal_ids(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    test_sample_internal_id: str,
):
    """Test to get sample internal ids from BclConvertMetricsParser."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting sample internal ids
    sample_internal_ids: list[str] = parsed_bcl_convert_metrics.get_sample_internal_ids()

    # THEN assert that the test sample internal id is present
    assert test_sample_internal_id in sample_internal_ids

    # THEN assert that all sample internal ids contain ACC prefix
    assert all([sample_internal_id.startswith("ACC") for sample_internal_id in sample_internal_ids])

    # THEN assert that all sample internal ids are unique
    assert len(sample_internal_ids) == len(set(sample_internal_ids))


def test_get_lanes_for_sample_internal_id(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser, test_sample_internal_id: str
):
    """Test to get lanes for a sample internal id from BclConvertMetricsParser."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting lanes for a sample internal id
    lanes: list[int] = parsed_bcl_convert_metrics.get_lanes_for_sample(
        sample_internal_id=test_sample_internal_id
    )

    # THEN assert that there are two lanes
    assert len(lanes) == 2
    for lane in lanes:
        assert isinstance(lane, int)
        assert lane in [1, 2]


def test_get_metrics_for_sample_internal_id_and_lane(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser, test_sample_internal_id: str
):
    """Test to get metrics for a sample internal id and lane from BclConvertMetricsParser."""

    # GIVEN a parsed BCLConvert metrics

    # WHEN getting metrics for a sample internal id and lane
    metrics: DemuxMetrics = parsed_bcl_convert_metrics.get_metrics_for_sample_and_lane(
        metrics=parsed_bcl_convert_metrics.demux_metrics,
        sample_internal_id=test_sample_internal_id,
        lane=1,
    )

    # THEN assert that the metrics are of the correct type
    assert isinstance(metrics, DemuxMetrics)
    assert metrics.sample_internal_id == test_sample_internal_id
    assert metrics.lane == 1


def test_calculate_total_reads_per_lane(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    test_sample_internal_id: str,
    bcl_convert_reads_for_test_sample: int,
    test_lane: int,
):
    """Test to calculate total reads per lane from BclConvertMetricsParser."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN calculating total reads per lane
    total_reads_per_lane: int = parsed_bcl_convert_metrics.calculate_total_reads_for_sample_in_lane(
        sample_internal_id=test_sample_internal_id, lane=test_lane
    )
    expected_total_reads_per_lane: int = bcl_convert_reads_for_test_sample * 2
    # THEN assert that the total reads per lane is correct
    assert total_reads_per_lane == expected_total_reads_per_lane


def test_get_q30_bases_percent_per_lane(
    parsed_bcl_convert_metrics,
    bcl_convert_test_q30_bases_percent: float,
    test_lane: int,
    test_sample_internal_id,
):
    """Test to get q30 bases percent per lane from BclConvertMetricsParser."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting q30 bases percent per lane
    q30_bases_percent_per_lane: float = (
        parsed_bcl_convert_metrics.get_q30_bases_percent_for_sample_in_lane(
            sample_internal_id=test_sample_internal_id, lane=test_lane
        )
    )

    # THEN assert that the q30 bases percent per lane is correct
    assert q30_bases_percent_per_lane == bcl_convert_test_q30_bases_percent


def test_get_mean_quality_score_per_lane(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    test_sample_internal_id: str,
    test_lane: int,
    bcl_convert_test_mean_quality_score_per_lane: float,
):
    """Test to get mean quality score per lane from BclConvertMetricsParser."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting mean quality score per lane
    mean_quality_score_per_lane: float = (
        parsed_bcl_convert_metrics.get_mean_quality_score_for_sample_in_lane(
            sample_internal_id=test_sample_internal_id, lane=test_lane
        )
    )

    # THEN assert that the mean quality score per lane is correct
    assert mean_quality_score_per_lane == bcl_convert_test_mean_quality_score_per_lane


def test_get_aggregate_total_reads_for_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    expected_aggegrated_reads: int,
):
    """Test to get the aggregate total reads for metrics."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting the aggregate total reads for metrics
    aggregate_total_reads: int = parsed_bcl_convert_metrics.get_total_reads_for_flow_cell()

    # THEN assert that the aggregate total reads is correct
    assert aggregate_total_reads == expected_aggegrated_reads


def test_get_aggregate_undetermined_reads_for_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    expected_aggregated_undetermined_reads: int,
):
    """Test to get the aggregated undetermined reads for metrics."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting the aggregated undetermined reads for metrics
    aggregated_undetermined_reads: int = (
        parsed_bcl_convert_metrics.get_undetermined_reads_for_flow_cell()
    )

    # THEN assert that the aggregated undetermined reads is correct
    assert aggregated_undetermined_reads == expected_aggregated_undetermined_reads


def test_get_aggregate_percent_q30_for_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    expected_aggregated_percent_q30: float,
):
    """Test to get the aggregate percent q30 for metrics."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting the aggregate percent q30 for metrics
    aggregate_percent_q30: float = parsed_bcl_convert_metrics.get_mean_percent_q30_for_flow_cell()

    # THEN assert that the aggregate percent q30 is correct
    assert aggregate_percent_q30 == expected_aggregated_percent_q30


def test_get_aggregate_quality_score_for_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    expected_aggregated_quality_score: float,
):
    """Test to get the aggregate quality score for metrics."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting the aggregate quality score for metrics
    aggregate_quality_score: float = (
        parsed_bcl_convert_metrics.get_mean_quality_score_sum_for_flow_cell()
    )

    # THEN assert that the aggregate quality score is correct
    assert aggregate_quality_score == expected_aggregated_quality_score


def test_get_aggregate_yield_for_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    expected_aggegrated_yield: int,
):
    """Test to get the aggregate yield for metrics."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting the aggregate yield for metrics
    aggregate_yield: int = parsed_bcl_convert_metrics.get_yield_for_flow_cell()

    # THEN assert that the aggregate yield is correct
    assert aggregate_yield == expected_aggegrated_yield


def test_get_aggregate_yield_q30_for_metrics(
    parsed_bcl_convert_metrics: BCLConvertMetricsParser,
    expected_aggegrated_yield_q30: int,
):
    """Test to get the aggregate yield Q30 for metrics."""
    # GIVEN a parsed BCLConvert metrics

    # WHEN getting the aggregate yield Q30 for metrics
    aggregate_yield_q30: int = parsed_bcl_convert_metrics.get_yield_q30_for_flow_cell()

    # THEN assert that the aggregate yield Q30 is correct
    assert aggregate_yield_q30 == expected_aggegrated_yield_q30
