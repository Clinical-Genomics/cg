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
def pac_bio_test_run_dir(pac_bio_runs_dir: Path, pac_bio_test_run_name: str) -> Path:
    """Return the path to a PacBio run directory."""
    return Path(pac_bio_runs_dir, pac_bio_test_run_name)


@pytest.fixture
def pac_bio_smrt_cell_dir(pac_bio_test_run_dir: Path) -> Path:
    """Return the path to a PacBio SMRT cell directory."""
    return Path(pac_bio_test_run_dir, "1_A01")


@pytest.fixture
def pac_bio_run_statistics_dir(pac_bio_smrt_cell_dir: Path) -> Path:
    """Return the path to the PacBio SMRT cell statistics directory."""
    return Path(pac_bio_smrt_cell_dir, "statistics")


# File fixtures


@pytest.fixture
def pac_bio_css_report(pac_bio_run_statistics_dir: Path) -> Path:
    """Return the path to the PacBio CSS report."""
    return Path(pac_bio_run_statistics_dir, PacBioDirsAndFiles.BASECALLING_REPORT)
