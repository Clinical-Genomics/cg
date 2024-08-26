"""Module for PacBio fixtures returning strings."""

import pytest


@pytest.fixture
def pac_bio_smrt_cell_name() -> str:
    return "1_A01"


@pytest.fixture
def pac_bio_test_run_name() -> str:
    """Return the name of a PacBio SMRT cell."""
    return "r84202_20240522_133539"


@pytest.fixture
def pac_bio_sequencing_run_name(pac_bio_test_run_name: str, pac_bio_smrt_cell_name: str) -> str:
    """Return the name of a PacBio SMRT cell."""
    return f"{pac_bio_test_run_name}/{pac_bio_smrt_cell_name})"


@pytest.fixture
def pac_bio_1_a01_cell_full_name() -> str:
    """Return the full name of a PacBio SMRT cell."""
    return "m84202_240522_135641_s1"


@pytest.fixture
def smrt_cell_internal_id() -> str:
    return "EA094834"


@pytest.fixture
def pac_bio_sample_internal_id() -> str:
    return "1247014000119"
