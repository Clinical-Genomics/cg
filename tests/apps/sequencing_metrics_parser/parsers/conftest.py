import pytest
from typing import Dict, List


@pytest.fixture
def flow_cell_name() -> str:
    """The unique identifier for the flow cell used in the sequencing run in the bcl2fastq stats.json output."""
    return "FLOW_CELL_NAME"


@pytest.fixture
def perfect_reads() -> int:
    return 33476720


@pytest.fixture
def mismatch_count() -> int:
    return 7860872


@pytest.fixture
def mismatch_counts(perfect_reads: int, mismatch_count: int) -> Dict:
    """The number of mismatches found when comparing the index sequence to the actual sequence in the bcl2fastq stats.json output."""
    return {"0": perfect_reads, "1": mismatch_count}


@pytest.fixture
def index_metrics(mismatch_counts: int) -> Dict:
    """Contains information about the index used for demultiplexing as structured in the bcl2fastq stats.json output."""
    return [{"MismatchCounts": mismatch_counts}]


@pytest.fixture
def yield_values() -> List[int]:
    """The total number of bases sequenced in two reads."""
    return [4464174570, 4464174570]


@pytest.fixture
def yield_q30_values() -> List[int]:
    """The number of bases with a Q30 quality score or higher in two reads."""
    return [4072773293, 3466288032]


@pytest.fixture
def lane_read_quality_score_values() -> List[int]:
    """The sum of the quality scores for all bases in two reads."""
    return [169586883451, 153047287631]


@pytest.fixture
def read_metrics(
    yield_values: List[int], yield_q30_values: List[int], lane_read_quality_score_values: List[int]
) -> Dict:
    """Read metrics as structured in the bcl2fastq stats.json output."""
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
def demux_result(
    read_metrics: Dict, index_metrics: Dict, sample_id: str, number_of_reads: int
) -> Dict:
    """Demux result as structured in the bcl2fastq stats.json output."""
    return {
        "SampleId": sample_id,
        "NumberReads": number_of_reads,
        "ReadMetrics": read_metrics,
        "IndexMetrics": index_metrics,
    }


@pytest.fixture
def lane_number() -> int:
    """Lane identifier."""
    return 1


@pytest.fixture
def lane_yield_in_bases() -> int:
    """The total number of bases sequenced in the lane."""
    return 8928349140


@pytest.fixture
def total_clusters_passing_filter() -> int:
    """The total number of clusters in the lane that passed filter (PF)."""
    return 215544263


@pytest.fixture
def total_raw_clusters() -> int:
    """The total number of clusters in the lane before filtering."""
    return 310605552


@pytest.fixture
def conversion_result(
    demux_result: Dict,
    lane_number: int,
    lane_yield_in_bases: int,
    total_clusters_passing_filter: int,
    total_raw_clusters: int,
) -> Dict:
    """Conversion result as structured in the bcl2fastq stats.json output."""
    return {
        "LaneNumber": lane_number,
        "DemuxResults": [demux_result],
        "Yield": lane_yield_in_bases,
        "TotalClustersPF": total_clusters_passing_filter,
        "TotalClustersRaw": total_raw_clusters,
    }


@pytest.fixture
def sequencing_metrics_json(conversion_result: Dict, flow_cell_name: str) -> Dict:
    """Structure of the bcl2fastq stats.json output."""
    return {
        "Flowcell": flow_cell_name,
        "ReadInfosForLanes": [{"LaneNumber": 1}],
        "ConversionResults": [conversion_result],
    }
