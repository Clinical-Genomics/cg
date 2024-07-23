"""Module for PacBio fixtures returning strings."""

import pytest


@pytest.fixture
def pac_bio_test_run_name() -> str:
    """Return the name of a PacBio SMRT cell."""
    return "r84202_20240522_133539"
