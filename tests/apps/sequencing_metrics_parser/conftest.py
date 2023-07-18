"""Fixtures for the sequencing metrics parser tests."""
from pathlib import Path
from cg.apps.sequencing_metrics_parser.models.bcl_convert import (
    BclConvertDemuxMetrics,
    BclConvertQualityMetrics,
    BclConvertSampleSheetData,
    BclConvertAdapterMetrics,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser
import pytest
from cg.constants.bcl_convert_metrics import (
    BclConvertQualityMetricsColumnNames,
    BclConvertDemuxMetricsColumnNames,
    BclConvertAdapterMetricsColumnNames,
)
from cg.constants.demultiplexing import SampleSheetNovaSeq6000Sections
from cg.store.models import SampleLaneSequencingMetrics
from datetime import datetime


@pytest.fixture(name="bcl_convert_metrics_dir_path", scope="session")
def fixture_bcl_convert_metrics_dir_path() -> Path:
    """Return a path to a BCLConvert metrics directory."""
    return Path(
        "tests", "fixtures", "apps", "sequencing_metrics_parser", "230622_A00621_0864_AHY7FFDRX2"
    )


@pytest.fixture(name="test_sample_internal_id", scope="session")
def fixture_test_sample_internal_id() -> str:
    """Return a test sample internal id."""
    return "ACC11927A2"


@pytest.fixture(name="test_sample_project", scope="session")
def fixture_test_sample_project() -> str:
    """Return a test sample project."""
    return "405887"


@pytest.fixture(name="test_lane", scope="session")
def fixture_test_lane() -> int:
    """Return a test lane."""
    return 1


@pytest.fixture(name="bcl_convert_reads_for_test_sample", scope="session")
def fixture_bcl_convert_reads_for_test_sample() -> int:
    """Return the number of reads for the test sample."""
    return 15962796


@pytest.fixture(name="bcl_convert_test_q30_bases_percent", scope="session")
def fixture_bcl_convert_test_q30_bases_percent() -> float:
    """Return the Q30 bases percent for the test sample."""
    return 0.94


@pytest.fixture(name="bcl_convert_test_mean_quality_score_per_lane", scope="session")
def fixture_bcl_convert_test_mean_quality_score() -> float:
    """Return the mean quality score for the test sample."""
    return 36.02


@pytest.fixture(name="bcl_convert_test_flow_cell_name", scope="session")
def fixture_bcl_convert_test_flow_cell_name() -> str:
    """Return the flow cell name for the test sample."""
    return "HY7FFDRX2"


@pytest.fixture(name="bcl_convert_demux_metric_model_with_data", scope="session")
def fixture_bcl_convert_demux_metric_model_with_data(
    test_lane,
    test_sample_internal_id,
    test_sample_project,
) -> BclConvertDemuxMetrics:
    """Return a BclConvertDemuxMetrics model with data."""
    return BclConvertDemuxMetrics(
        **{
            BclConvertDemuxMetricsColumnNames.LANE.value: test_lane,
            BclConvertDemuxMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            BclConvertDemuxMetricsColumnNames.SAMPLE_PROJECT.value: test_sample_project,
            BclConvertDemuxMetricsColumnNames.READ_PAIR_COUNT.value: 15962796,
            BclConvertDemuxMetricsColumnNames.PERFECT_INDEX_READS_COUNT.value: 15962796,
            BclConvertDemuxMetricsColumnNames.PERFECT_INDEX_READS_PERCENT.value: 1.0000,
            BclConvertDemuxMetricsColumnNames.ONE_MISMATCH_INDEX_READS_COUNT.value: 0,
            BclConvertDemuxMetricsColumnNames.TWO_MISMATCH_INDEX_READS_COUNT.value: 0,
        }
    )


@pytest.fixture(name="bcl_convert_adapter_metric_model_with_data", scope="session")
def fixture_bcl_convert_adapter_metric_model_with_data(
    test_lane, test_sample_internal_id, test_sample_project
) -> BclConvertAdapterMetrics:
    """Return a BclConvertAdapterMetrics model with data."""
    return BclConvertAdapterMetrics(
        **{
            BclConvertAdapterMetricsColumnNames.LANE.value: test_lane,
            BclConvertAdapterMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            BclConvertAdapterMetricsColumnNames.SAMPLE_PROJECT.value: test_sample_project,
            BclConvertAdapterMetricsColumnNames.READ_NUMBER.value: 1,
            BclConvertAdapterMetricsColumnNames.SAMPLE_BASES.value: 415032696,
        }
    )


@pytest.fixture(name="bcl_convert_quality_metric_model_with_data", scope="session")
def fixture_bcl_convert_quality_metric_model_with_data(
    test_lane, test_sample_internal_id, test_sample_project
) -> BclConvertQualityMetrics:
    """Return a BclConvertQualityMetrics model with data."""
    return BclConvertQualityMetrics(
        **{
            BclConvertQualityMetricsColumnNames.LANE.value: test_lane,
            BclConvertQualityMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            BclConvertQualityMetricsColumnNames.READ_PAIR_NUMBER.value: 1,
            BclConvertQualityMetricsColumnNames.YIELD_BASES.value: 415032696,
            BclConvertQualityMetricsColumnNames.YIELD_Q30.value: 393745856,
            BclConvertQualityMetricsColumnNames.QUALITY_SCORE_SUM.value: 15004333259,
            BclConvertQualityMetricsColumnNames.MEAN_QUALITY_SCORE_Q30.value: 36.15,
            BclConvertQualityMetricsColumnNames.Q30_BASES_PERCENT.value: 0.95,
        }
    )


@pytest.fixture(name="bcl_convert_sample_sheet_model_with_data", scope="session")
def fixture_bcl_convert_sample_sheet_model_with_data(
    test_lane,
    test_sample_internal_id,
    test_sample_project,
) -> BclConvertSampleSheetData:
    """Return a BclConvertSampleSheetData model with data."""
    return BclConvertSampleSheetData(
        **{
            SampleSheetNovaSeq6000Sections.Data.FLOW_CELL_ID.value: "HY7FFDRX2",
            SampleSheetNovaSeq6000Sections.Data.LANE.value: test_lane,
            SampleSheetNovaSeq6000Sections.Data.SAMPLE_INTERNAL_ID_BCLCONVERT.value: test_sample_internal_id,
            SampleSheetNovaSeq6000Sections.Data.SAMPLE_NAME.value: "anonymous_1",
            SampleSheetNovaSeq6000Sections.Data.CONTROL.value: "N",
            SampleSheetNovaSeq6000Sections.Data.SAMPLE_PROJECT_BCLCONVERT.value: test_sample_project,
        }
    )


@pytest.fixture(name="parsed_bcl_convert_metrics", scope="session")
def fixture_parsed_bcl_convert_metrics(bcl_convert_metrics_dir_path) -> BclConvertMetricsParser:
    """Return an object with parsed BCLConvert metrics."""
    return BclConvertMetricsParser(bcl_convert_metrics_dir_path=bcl_convert_metrics_dir_path)


@pytest.fixture(name="parsed_sequencing_statistics_from_bcl_convert", scope="session")
def fixture_parsed_sequencing_statistics_from_bcl_convert(
    test_sample_internal_id: str,
    test_lane: int,
    bcl_convert_test_flow_cell_name: str,
    bcl_convert_reads_for_test_sample: int,
    bcl_convert_test_mean_quality_score_per_lane: float,
    bcl_convert_test_q30_bases_percent_per_lane: float,
) -> SampleLaneSequencingMetrics:
    return SampleLaneSequencingMetrics(
        sample_internal_id=test_sample_internal_id,
        flow_cell_lane_number=test_lane,
        flow_cell_name=bcl_convert_test_flow_cell_name,
        sample_total_reads_in_lane=bcl_convert_reads_for_test_sample * 2,
        sample_base_mean_quality_score=bcl_convert_test_mean_quality_score_per_lane,
        sample_base_fraction_passing_q30=bcl_convert_test_q30_bases_percent_per_lane,
        created_at=datetime.now(),
    )
