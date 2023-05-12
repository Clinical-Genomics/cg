from cg.apps.sequencing_metrics_parser import (
    get_yield_values,
    get_read_metrics,
    get_index_metrics,
    get_flow_cell_name,
    get_sample_id,
    get_number_of_reads_for_sample_in_lane,
    get_lane_number,
    get_yield_q30,
)


def test_get_flow_cell_name(bcl2fastq_sequencing_metrics_data, flow_cell_name):
    assert get_flow_cell_name(bcl2fastq_sequencing_metrics_data) == flow_cell_name


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
