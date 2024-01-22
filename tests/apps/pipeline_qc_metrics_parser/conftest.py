"""Fixtures for the pipeline qc metrics parser."""
from pathlib import Path

import pytest


@pytest.fixture()
def mip_dna_pipeline_qc_metrics_file_name() -> str:
    return "mip_dna_pipeline_qc_metrics.json"


@pytest.fixture()
def mip_dna_pipeline_qc_metrics_path(
    fixtures_dir: Path, mip_dna_pipeline_qc_metrics_file_name: str
) -> Path:
    return Path(fixtures_dir, "apps", "pipeline_qc_metrics", mip_dna_pipeline_qc_metrics_file_name)
