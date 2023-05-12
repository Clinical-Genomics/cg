import pytest


@pytest.fixture
def flow_cell_name():
    return "FLOW_CELL_NAME"


@pytest.fixture
def bcl2fastq_sequencing_metrics_data(flow_cell_name):
    return {"Flowcell": flow_cell_name}


@pytest.fixture
def perfect_reads():
    return 33476720


@pytest.fixture
def mismatch_counts(perfect_reads):
    return {"0": perfect_reads, "1": 7860872}


@pytest.fixture
def index_metrics(mismatch_counts):
    return [{"MismatchCounts": mismatch_counts}]


@pytest.fixture
def yield_values():
    return [4464174570, 4464174570]


@pytest.fixture
def yield_q30_values():
    return [4072773293, 3466288032]


@pytest.fixture
def lane_read_quality_score_values():
    return [169586883451, 153047287631]


@pytest.fixture
def read_metrics(yield_values, yield_q30_values, lane_read_quality_score_values):
    return [
        {
            "Yield": yield_values[0],
            "YieldQ30": yield_q30_values[0],
            "QualityScoreSum": lane_read_quality_score_values[0],
        },
        {
            "Yield": yield_values[1],
            "YieldQ30": yield_q30_values[1],
            "QualityScoreSum": lane_read_quality_score_values[1],
        },
    ]


@pytest.fixture
def number_of_reads():
    return 29564070


@pytest.fixture
def yield_q30():
    4072773293


@pytest.fixture
def demux_result(read_metrics, index_metrics, sample_id, number_of_reads):
    return {
        "SampleId": sample_id,
        "NumberReads": number_of_reads,
        "ReadMetrics": read_metrics,
        "IndexMetrics": index_metrics,
    }


@pytest.fixture
def lane_number():
    return 1


@pytest.fixture
def lane_yield_in_bases():
    return 8928349140


@pytest.fixture
def total_clusters_passing_filter():
    return 215544263


@pytest.fixture
def total_raw_clusters():
    return 310605552


@pytest.fixture
def conversion_result(
    demux_result,
    lane_number,
    lane_yield_in_bases,
    total_clusters_passing_filter,
    total_raw_clusters,
):
    return {
        "LaneNumber": lane_number,
        "DemuxResults": [demux_result],
        "Yield": lane_yield_in_bases,
        "TotalClustersPF": total_clusters_passing_filter,
        "TotalClustersRaw": total_raw_clusters,
    }
