"""Module for PacBio fixtures returning Path objects."""

from pathlib import Path

import pytest

from cg.constants.pacbio import PacBioDirsAndFiles


# Directory fixtures
@pytest.fixture
def pac_bio_fixtures_dir(devices_dir: Path) -> Path:
    """Return the path to the PacBio fixtures directory."""
    return Path(devices_dir, "pacbio")


@pytest.fixture
def pac_bio_runs_dir(pac_bio_fixtures_dir: Path) -> Path:
    """Return the path to the PacBio run directory."""
    return Path(pac_bio_fixtures_dir, "SMRTcells")


@pytest.fixture
def pac_bio_smrt_cell_dir(pac_bio_runs_dir: Path, pac_bio_smrt_cell_name: str) -> Path:
    """Return the path to the PacBio run directory."""
    return Path(pac_bio_runs_dir, pac_bio_smrt_cell_name)


@pytest.fixture
def pac_bio_run_statistics_dir(pac_bio_run_dir: Path) -> Path:
    """Return the path to the PacBio run statistics directory."""
    return Path(pac_bio_run_dir, "statistics")


# File fixtures


@pytest.fixture
def pac_bio_css_report(pac_bio_run_statistics_dir: Path) -> Path:
    """Return the path to the PacBio CSS report."""
    return Path(pac_bio_run_statistics_dir, PacBioDirsAndFiles.CSS_REPORT)
