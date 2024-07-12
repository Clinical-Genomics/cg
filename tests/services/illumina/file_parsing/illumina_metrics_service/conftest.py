"""Fixtures for the sequencing metrics parser tests."""

from pathlib import Path

import pytest

from cg.constants.metrics import DemuxMetricsColumnNames, QualityMetricsColumnNames
from cg.services.illumina.file_parsing.models import (
    DemuxMetrics,
    SequencingQualityMetrics,
)
from cg.services.illumina.file_parsing.bcl_convert_metrics_parser import (
    BCLConvertMetricsParser,
)


@pytest.fixture(scope="session")
def bcl_convert_metrics_dir_path() -> Path:
    """Return a path to a BCLConvert metrics directory."""
    return Path(
        "tests",
        "fixtures",
        "services",
        "illumina",
        "file_parsing",
        "230622_A00621_0864_AHY7FFDRX2",
    )


@pytest.fixture(scope="session")
def test_sample_internal_id() -> str:
    """Return a test sample internal id."""
    return "ACC11927A2"


@pytest.fixture(scope="session")
def test_lane() -> int:
    """Return a test lane."""
    return 1


@pytest.fixture(scope="session")
def bcl_convert_reads_for_test_sample() -> int:
    """Return the number of reads for the test sample."""
    return 15962796


@pytest.fixture(scope="session")
def bcl_convert_test_q30_bases_percent() -> float:
    """Return the Q30 bases percent for the test sample."""
    return 94


@pytest.fixture(scope="session")
def bcl_convert_test_mean_quality_score_per_lane() -> float:
    """Return the mean quality score for the test sample."""
    return 36.02


@pytest.fixture(scope="session")
def bcl_convert_demux_metric_model_with_data(
    test_lane,
    test_sample_internal_id,
) -> DemuxMetrics:
    """Return a BclConvertDemuxMetrics model with data."""
    return DemuxMetrics(
        **{
            DemuxMetricsColumnNames.LANE.value: test_lane,
            DemuxMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            DemuxMetricsColumnNames.READ_PAIR_COUNT.value: 15962796,
        }
    )


@pytest.fixture(scope="session")
def bcl_convert_quality_metric_model_with_data(
    test_lane, test_sample_internal_id
) -> SequencingQualityMetrics:
    """Return a BclConvertQualityMetrics model with data."""
    return SequencingQualityMetrics(
        **{
            QualityMetricsColumnNames.LANE.value: test_lane,
            QualityMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            QualityMetricsColumnNames.MEAN_QUALITY_SCORE_Q30.value: 36.15,
            QualityMetricsColumnNames.Q30_BASES_PERCENT.value: 0.95,
            QualityMetricsColumnNames.QUALITY_SCORE_SUM.value: 15004333259,
            QualityMetricsColumnNames.YIELD.value: 415032696,
            QualityMetricsColumnNames.YIELD_Q30.value: 393745856,
        }
    )


@pytest.fixture(scope="session")
def parsed_bcl_convert_metrics(bcl_convert_metrics_dir_path) -> BCLConvertMetricsParser:
    """Return an object with parsed BCLConvert metrics."""
    return BCLConvertMetricsParser(bcl_convert_metrics_dir_path=bcl_convert_metrics_dir_path)


@pytest.fixture(scope="session")
def expected_aggegrated_reads() -> int:
    """Return the expected aggregated reads for metrics file."""
    return 1458658700


@pytest.fixture(scope="session")
def expected_aggregated_undetermined_reads() -> int:
    """Return the expected aggregated undetermined reads for metrics file."""
    return 154578798


@pytest.fixture(scope="session")
def expected_aggregated_percent_q30() -> float:
    """Return the expected aggregated percent Q30 for metrics file."""
    return 92.00


@pytest.fixture(scope="session")
def expected_aggregated_quality_score() -> float:
    """Return the expected aggregated quality score for metrics file."""
    return 35.6


@pytest.fixture(scope="session")
def expected_aggegrated_yield() -> int:
    """Return the expected aggregated yield for metrics file."""
    return 84610417748


@pytest.fixture(scope="session")
def expected_aggegrated_yield_q30() -> int:
    """Return the expected aggregated yield Q30 for metrics file."""
    return 78046839027
