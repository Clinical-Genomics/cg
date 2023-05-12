"""Fixtures for the sequencing metics parser tests."""
from pathlib import Path
import pytest


@pytest.fixture(name="bcl_convert_demux_metric_file_path")
def fixture_bcl_convert_demux_metric_file_path() -> Path:
    """Return a path to a BCLConvert demux metrics file."""
    return Path("tests/fixtures/apps/sequencing_metrics_parser/bcl_convert_metrics.csv")


@pytest.fixture(name="bcl_convert_quality_metric_file_path")
def fixture_bcl_convert_quality_metric_file_path() -> Path:
    """Return a path to a BCLConvert quality metrics file."""
    return Path("tests/fixtures/apps/sequencing_metrics_parser/bcl_convert_quality_metrics.csv")


@pytest.fixture(name="bcl_convert_sample_sheet_file_path")
def fixture_bcl_convert_sample_sheet_file_path() -> Path:
    """Return a path to a BCLConvert sample sheet file."""
    return Path("tests/fixtures/apps/sequencing_metrics_parser/bcl_convert_sample_sheet.csv")


@pytest.fixture(name="bcl_convert_adapter_metrics_file_path")
def fixture_bcl_convert_adapter_metrics_file_path() -> Path:
    """Return a path to a BCLConvert adapter metrics file."""
    return Path("tests/fixtures/apps/sequencing_metrics_parser/bcl_convert_adapter_metrics.csv")


@pytest.fixture(name="bcl_convert_run_info_file_path")
def fixture_bcl_convert_run_info_file_path() -> Path:
    """Return a path to a BCLConvert run info file."""
    return Path("tests/fixtures/apps/sequencing_metrics_parser/bcl_convert_run_info.xml")
