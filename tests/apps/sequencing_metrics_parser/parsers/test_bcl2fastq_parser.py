from typing import Dict, List
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


def test_get_flow_cell_name(sequencing_metrics_json: Dict, flow_cell_name: str):
    # GIVEN the stats.json output from bcl2fastq
    # WHEN parsing the flow cell name from the json
    parsed_flow_cell_name = get_flow_cell_name(sequencing_metrics_json)

    # THEN assert that the flow cell name is the expected one
    assert parsed_flow_cell_name == flow_cell_name


def test_get_read_metrics(demux_result: Dict, read_metrics: Dict):
    # GIVEN the demux result object from bcl2fastq stats.json output
    # WHEN parsing the read metrics from the json object
    parsed_read_metrics = get_read_metrics(demux_result)

    # THEN the parsed read metrics should be the expected one
    assert parsed_read_metrics == read_metrics


def test_get_index_metrics(demux_result: Dict, index_metrics: Dict):
    # GIVEN the demux result object from bcl2fastq stats.json output
    # WHEN parsing the index metrics from the json object
    parsed_index_metrics = get_index_metrics(demux_result)

    # THEN the parsed index metrics should be the one in the demux object
    assert parsed_index_metrics == index_metrics[0]


def test_get_yield_values(demux_result: Dict, yield_values: List[int]):
    # GIVEN the demux result object from bcl2fastq stats.json output
    # WHEN parsing the yield values from the json object
    parsed_yield_values = get_yield_values(demux_result)

    # THEN the parsed yield values should be the one in the demux object
    assert parsed_yield_values == yield_values


def test_get_sample_id(demux_result: Dict, sample_id: str):
    # GIVEN the demux result object from bcl2fastq stats.json output
    # WHEN parsing the sample id from the json object
    parsed_sample_id = get_sample_id(demux_result)

    # THEN the parsed sample id should be the one in the demux object
    assert parsed_sample_id == sample_id


def test_get_number_of_reads_for_sample_in_lane(demux_result: Dict, number_of_reads: int):
    # GIVEN the demux result object from bcl2fastq stats.json output
    # WHEN parsing the number of reads for sample in lane from the json object
    parsed_number_of_reads = get_number_of_reads_for_sample_in_lane(demux_result)

    # THEN the parsed number of reads should be the one in the demux object
    assert parsed_number_of_reads == number_of_reads


def test_get_lane_number(conversion_result: Dict, lane_number: int):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing the lane number from the json object
    parsed_lane_number = get_lane_number(conversion_result)

    # THEN the parsed lane number should be the one in the conversion object
    assert parsed_lane_number == lane_number


def test_get_yield_q30(read_metrics: List[Dict], yield_q30_values):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing the yield q30 values from the json object
    parsed_yield_q30_values = get_yield_q30(read_metrics[0])

    # THEN the parsed yield q30 values should be the ones in the conversion object
    assert parsed_yield_q30_values == yield_q30_values[0]


def test_get_lane_yield_in_bases(conversion_result: Dict, lane_yield_in_bases):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing the lane yield in bases from the json object
    parsed_lane_yield_in_bases = get_lane_yield_in_bases(conversion_result)

    # THEN the parsed lane yield in bases should be the one in the conversion object
    assert parsed_lane_yield_in_bases == lane_yield_in_bases


def test_get_total_clusters_passing_filter(conversion_result: Dict, total_clusters_passing_filter):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing the total clusters passing filter from the json object
    parsed_total_clusters_passing_filter = get_total_clusters_passing_filter(conversion_result)

    # THEN the parsed total clusters passing filter should be the one in the conversion object
    assert parsed_total_clusters_passing_filter == total_clusters_passing_filter


def test_get_total_raw_clusters(conversion_result: Dict, total_raw_clusters):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing the total raw clusters from the json object
    parsed_total_raw_clusters = get_total_raw_clusters(conversion_result)

    # THEN the parsed total raw clusters should be the one in the conversion object
    assert parsed_total_raw_clusters == total_raw_clusters


def test_get_lane_yield_q30_values(demux_result: Dict, yield_q30_values):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing the lane yield q30 values from the json object
    parsed_lane_yield_q30_values = get_lane_yield_q30_values(demux_result)

    # THEN the parsed lane yield q30 values should be the one in the conversion object
    assert parsed_lane_yield_q30_values == yield_q30_values


def test_get_lane_read_quality_score_values(
    demux_result: Dict, lane_read_quality_score_values: List[int]
):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing the lane read quality score values from the json object
    parsed_lane_read_quality_score_values = get_lane_read_quality_score_values(demux_result)

    # THEN the parsed lane read quality score values should be the one in the conversion object
    assert parsed_lane_read_quality_score_values == lane_read_quality_score_values


def test_get_quality_score(read_metrics: List[Dict], lane_read_quality_score_values: List[int]):
    # GIVEN the conversion result object from bcl2fastq stats.json output
    # WHEN parsing parsing the quality score from the json object
    parsed_quality_score = get_quality_score(read_metrics[0])

    # THEN the parsed quality score should be the one in the conversion object
    assert parsed_quality_score == lane_read_quality_score_values[0]


def test_get_perfect_reads_for_sample_in_lane(demux_result: Dict, perfect_reads: int):
    # GIVEN the demux result object from bcl2fastq stats.json output
    # WHEN parsing the perfect reads for sample in lane from the json object
    parsed_perfect_reads = get_perfect_reads_for_sample_in_lane(demux_result)

    # THEN the parsed perfect reads should be the one in the demux object
    assert parsed_perfect_reads == perfect_reads


@mock.patch("cg.apps.sequencing_metrics_parser.parsers.bcl2fastq.read_json")
def test_parsing_json(mock_read_json, sequencing_metrics_json: Dict):
    # GIVEN a sequencing metrics file
    mock_read_json.return_value = sequencing_metrics_json

    # WNEN parsing the sequencing metrics from the file
    metrics = parse_bcl2fastq_sequencing_metrics("some_path")

    # THEN metrics should be returned
    assert metrics
    # THEN the metrics should be of type SequencingMetricsForLaneAndSample
    assert isinstance(metrics[0], SequencingMetricsForLaneAndSample)
