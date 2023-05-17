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
from cg.constants.demultiplexing import SampleSheetHeaderColumnNames


@pytest.fixture(name="bcl_convert_demux_metric_file_path")
def fixture_bcl_convert_demux_metric_file_path() -> Path:
    """Return a path to a BCLConvert demux metrics file."""
    return Path("tests", "fixtures", "apps", "sequencing_metrics_parser", "bcl_convert_metrics.csv")


@pytest.fixture(name="bcl_convert_quality_metric_file_path")
def fixture_bcl_convert_quality_metric_file_path() -> Path:
    """Return a path to a BCLConvert quality metrics file."""
    return Path(
        "tests", "fixtures", "apps", "sequencing_metrics_parser", "bcl_convert_quality_metrics.csv"
    )


@pytest.fixture(name="bcl_convert_sample_sheet_file_path")
def fixture_bcl_convert_sample_sheet_file_path() -> Path:
    """Return a path to a BCLConvert sample sheet file."""
    return Path(
        "tests", "fixtures", "apps", "sequencing_metrics_parser", "bcl_convert_sample_sheet.csv"
    )


@pytest.fixture(name="bcl_convert_adapter_metrics_file_path")
def fixture_bcl_convert_adapter_metrics_file_path() -> Path:
    """Return a path to a BCLConvert adapter metrics file."""
    return Path(
        "tests", "fixtures", "apps", "sequencing_metrics_parser", "bcl_convert_adapter_metrics.csv"
    )


@pytest.fixture(name="bcl_convert_run_info_file_path")
def fixture_bcl_convert_run_info_file_path() -> Path:
    """Return a path to a BCLConvert run info file."""
    return Path(
        "tests", "fixtures", "apps", "sequencing_metrics_parser", "bcl_convert_run_info.xml"
    )


@pytest.fixture(name="test_sample_internal_id")
def fixture_test_sample_internal_id() -> str:
    """Return a test sample internal id."""
    return "ACC11927A2"


@pytest.fixture(name="bcl_convert_demux_metric_model_with_data")
def fixture_bcl_convert_demux_metric_model_with_data(
    test_sample_internal_id,
) -> BclConvertDemuxMetrics:
    return BclConvertDemuxMetrics(
        **{
            BclConvertDemuxMetricsColumnNames.LANE.value: 1,
            BclConvertDemuxMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            BclConvertDemuxMetricsColumnNames.SAMPLE_PROJECT.value: "405887",
            BclConvertDemuxMetricsColumnNames.READ_PAIR_COUNT.value: 15962796,
            BclConvertDemuxMetricsColumnNames.PERFECT_INDEX_READS_COUNT.value: 15962796,
            BclConvertDemuxMetricsColumnNames.PERFECT_INDEX_READS_PERCENT.value: 1.0000,
            BclConvertDemuxMetricsColumnNames.ONE_MISMATCH_INDEX_READS_COUNT.value: 0,
            BclConvertDemuxMetricsColumnNames.TWO_MISMATCH_INDEX_READS_COUNT.value: 0,
        }
    )


@pytest.fixture(name="bcl_convert_adapter_metric_model_with_data")
def fixture_bcl_convert_adapter_metric_model_with_data(
    test_sample_internal_id,
) -> BclConvertAdapterMetrics:
    return BclConvertAdapterMetrics(
        **{
            BclConvertAdapterMetricsColumnNames.LANE.value: 1,
            BclConvertAdapterMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            BclConvertAdapterMetricsColumnNames.SAMPLE_PROJECT.value: "405887",
            BclConvertAdapterMetricsColumnNames.READ_NUMBER.value: 1,
            BclConvertAdapterMetricsColumnNames.SAMPLE_BASES.value: 415032696,
        }
    )


@pytest.fixture(name="bcl_convert_quality_metric_model_with_data")
def fixture_bcl_convert_quality_metric_model_with_data(
    test_sample_internal_id,
) -> BclConvertQualityMetrics:
    return BclConvertQualityMetrics(
        **{
            BclConvertQualityMetricsColumnNames.LANE.value: 1,
            BclConvertQualityMetricsColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            BclConvertQualityMetricsColumnNames.READ_PAIR_NUMBER.value: 1,
            BclConvertQualityMetricsColumnNames.YIELD_BASES.value: 415032696,
            BclConvertQualityMetricsColumnNames.YIELD_Q30.value: 393745856,
            BclConvertQualityMetricsColumnNames.QUALITY_SCORE_SUM.value: 15004333259,
            BclConvertQualityMetricsColumnNames.MEAN_QUALITY_SCORE_Q30.value: 36.15,
            BclConvertQualityMetricsColumnNames.Q30_BASES_PERCENT.value: 0.95,
        }
    )


@pytest.fixture(name="bcl_convert_sample_sheet_model_with_data")
def fixture_bcl_convert_sample_sheet_model_with_data(
    test_sample_internal_id,
) -> BclConvertSampleSheetData:
    return BclConvertSampleSheetData(
        **{
            SampleSheetHeaderColumnNames.FLOW_CELL_ID.value: "HY7FFDRX2",
            SampleSheetHeaderColumnNames.LANE.value: 1,
            SampleSheetHeaderColumnNames.SAMPLE_INTERNAL_ID.value: test_sample_internal_id,
            SampleSheetHeaderColumnNames.SAMPLE_NAME.value: "p023BCR",
            SampleSheetHeaderColumnNames.CONTROL.value: "N",
            SampleSheetHeaderColumnNames.SAMPLE_PROJECT.value: "405887",
        }
    )


@pytest.fixture(name="parsed_bcl_convert_metrics")
def fixture_parsed_bcl_convert_metrics(
    bcl_convert_quality_metric_file_path,
    bcl_convert_demux_metric_file_path,
    bcl_convert_sample_sheet_file_path,
    bcl_convert_adapter_metrics_file_path,
    bcl_convert_run_info_file_path,
) -> BclConvertMetricsParser:
    """Return a dictionary with parsed BCLConvert metrics."""
    return BclConvertMetricsParser(
        bcl_convert_quality_metrics_path=bcl_convert_quality_metric_file_path,
        bcl_convert_demux_metrics_file_path=bcl_convert_demux_metric_file_path,
        bcl_convert_sample_sheet_file_path=bcl_convert_sample_sheet_file_path,
        bcl_convert_adapter_metrics_file_path=bcl_convert_adapter_metrics_file_path,
        bcl_convert_run_info_file_path=bcl_convert_run_info_file_path,
    )
