"""Conftest for Gens."""

from pathlib import Path

import pytest


@pytest.fixture(name="gens_fracsnp_path")
def fixture_gens_fracsnp_path(analysis_dir: Path, sample_id: str) -> Path:
    """Path to Gens fracsnp/baf bed file."""
    return Path(analysis_dir, f"{sample_id}.baf.bed.gz")


@pytest.fixture(name="gens_coverage_path")
def fixture_gens_coverage_path(analysis_dir: Path, sample_id: str) -> Path:
    """Path to Gens coverage bed file."""
    return Path(analysis_dir, f"{sample_id}.cov.bed.gz")
