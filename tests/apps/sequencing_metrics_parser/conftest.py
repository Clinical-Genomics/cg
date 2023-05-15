"""Fixtures for the sequencing metics parser tests."""
from pathlib import Path
from cg.apps.sequencing_metrics_parser.models.bcl_convert import (
    BclConvertDemuxMetrics,
    BclConvertQualityMetrics,
    BclConvertSampleSheet,
    BclConvertAdapterMetrics,
)
import pytest


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
        lane=1,
        sample_internal_id=test_sample_internal_id,
        sample_project="405887",
        read_pair_count=15962796,
        perfect_index_reads_count=15962796,
        perfect_index_reads_percent=1.0000,
        one_mismatch_index_reads_count=0,
        two_mismatch_index_reads_count=0,
    )


@pytest.fixture(name="bcl_convert_adapter_metric_model_with_data")
def fixture_bcl_convert_adapter_metric_model_with_data(
    test_sample_internal_id,
) -> BclConvertAdapterMetrics:
    return BclConvertAdapterMetrics(
        lane=1,
        sample_internal_id=test_sample_internal_id,
        sample_project="405887",
        read_number=1,
        sample_bases=415032696,
    )


@pytest.fixture(name="bcl_convert_quality_metric_model_with_data")
def fixture_bcl_convert_quality_metric_model_with_data(
    test_sample_internal_id,
) -> BclConvertQualityMetrics:
    return BclConvertQualityMetrics(
        lane=1,
        sample_internal_id=test_sample_internal_id,
        read_pair_number=1,
        yield_bases=415032696,
        yield_q30_bases=393745856,
        quality_score_sum=15004333259,
        mean_quality_score_q30=36.15,
        q30_bases_percent=0.95,
    )


@pytest.fixture(name="bcl_convert_sample_sheet_model_with_data")
def fixture_bcl_convert_sample_sheet_model_with_data(
    test_sample_internal_id,
) -> BclConvertSampleSheet:
    return BclConvertSampleSheet(
        flow_cell_name="HY7FFDRX2",
        lane=1,
        sample_internal_id=test_sample_internal_id,
        sample_name="p023BCR",
        control="N",
        sample_project="405887",
    )
