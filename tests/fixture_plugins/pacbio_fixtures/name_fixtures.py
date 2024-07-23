"""Module for PacBio fixtures returning strings."""

import pytest

from cg.constants.pacbio import PacBioDirsAndFiles


@pytest.fixture
def pac_bio_test_run_name() -> str:
    """Return the name of a PacBio SMRT cell."""
    return "r84202_20240522_133539"


@pytest.fixture
def pac_bio_1_a01_cell_full_name() -> str:
    """Return the full name of a PacBio SMRT cell."""
    return "m84202_240522_135641_s1"


@pytest.fixture
def ccs_report_1_a01_name(pac_bio_1_a01_cell_full_name: str) -> str:
    """Return the name of a ccs report file."""
    return f"{pac_bio_1_a01_cell_full_name}.{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}"
