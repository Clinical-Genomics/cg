"""Fixtures for the sequencing metics parser tests."""
from pathlib import Path
import pytest


@pytest.fixture(name="bcl_convert_metric_file_path")
def fixture_bcl_convert_metric_file_path() -> Path:
    """Return a path to a BCLConvert metrics file."""
    return Path("tests/fixtures/apps/sequencing_metrics_parser/bcl_convert_metrics.csv")
