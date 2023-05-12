from unittest import mock
from cg.apps.sequencing_metrics_parser import (
    get_yield_values,
    get_read_metrics,
    get_index_metrics,
    get_flow_cell_name,
    get_sample_id,
    get_number_of_reads_for_sample_in_lane,
    get_lane_number,
    get_yield_q30,
    get_lane_yield_in_bases,
    get_total_clusters_passing_filter,
    get_total_raw_clusters,
    get_quality_score,
    get_lane_yield_q30_values,
    get_lane_read_quality_score_values,
    get_perfect_reads_for_sample_in_lane,
    parse_bcl2fastq_sequencing_metrics,
)
from cg.apps.sequencing_metrics_parser.models import SequencingMetricsForLaneAndSample


def test_get_flow_cell_name(sequencing_metrics_json, flow_cell_name):
    assert get_flow_cell_name(sequencing_metrics_json) == flow_cell_name


def test_get_read_metrics(demux_result, read_metrics):
    assert get_read_metrics(demux_result) == read_metrics


def test_get_index_metrics(demux_result, index_metrics):
    assert get_index_metrics(demux_result) == index_metrics[0]


def test_get_yield_values(demux_result, yield_values):
    assert get_yield_values(demux_result) == yield_values


def test_get_sample_id(demux_result, sample_id):
    assert get_sample_id(demux_result) == sample_id


def test_get_number_of_reads_for_sample_in_lane(demux_result, number_of_reads):
    assert get_number_of_reads_for_sample_in_lane(demux_result) == number_of_reads


def test_get_lane_number(conversion_result, lane_number):
    assert get_lane_number(conversion_result) == lane_number


def test_get_yield_q30(read_metrics, yield_q30_values):
    assert get_yield_q30(read_metrics[0]) == yield_q30_values[0]


def test_get_lane_yield_in_bases(conversion_result, lane_yield_in_bases):
    assert get_lane_yield_in_bases(conversion_result) == lane_yield_in_bases


def test_get_total_clusters_passing_filter(conversion_result, total_clusters_passing_filter):
    assert get_total_clusters_passing_filter(conversion_result) == total_clusters_passing_filter


def test_get_total_raw_clusters(conversion_result, total_raw_clusters):
    assert get_total_raw_clusters(conversion_result) == total_raw_clusters


def test_get_lane_yield_q30_values(demux_result, yield_q30_values):
    assert get_lane_yield_q30_values(demux_result) == yield_q30_values


def test_get_lane_read_quality_score_values(demux_result, lane_read_quality_score_values):
    assert get_lane_read_quality_score_values(demux_result) == lane_read_quality_score_values


def test_get_quality_score(read_metrics, lane_read_quality_score_values):
    assert get_quality_score(read_metrics[0]) == lane_read_quality_score_values[0]


def test_get_perfect_reads_for_sample_in_lane(demux_result, perfect_reads):
    assert get_perfect_reads_for_sample_in_lane(demux_result) == perfect_reads


@mock.patch("cg.apps.sequencing_metrics_parser.parsers.bcl2fastq.read_json")
def test_parsing_json(mock_read_json, sequencing_metrics_json):
    mock_read_json.return_value = sequencing_metrics_json
    metrics = parse_bcl2fastq_sequencing_metrics("some_path")

    assert metrics
    assert isinstance(metrics[0], SequencingMetricsForLaneAndSample)
