"""Module for PacBio fixtures returning strings."""

import pytest


@pytest.fixture
def pac_bio_smrt_cell_name() -> str:
    return "1_B01"


@pytest.fixture
def pacbio_barcoded_smrt_cell_name() -> str:
    return "1_C01"


@pytest.fixture
def pac_bio_test_run_id() -> str:
    """Return the run ID of a PacBio sequencing run."""
    return "r84202_20240522_133539"


@pytest.fixture
def pacbio_barcoded_run_id() -> str:
    return "r84202_20240913_121403"


@pytest.fixture
def pacbio_smrt_cell_full_name(pac_bio_test_run_id: str, pac_bio_smrt_cell_name: str) -> str:
    """Return the full name of a PacBio SMRT cell."""
    return f"{pac_bio_test_run_id}/{pac_bio_smrt_cell_name}"


@pytest.fixture
def pacbio_barcoded_smrt_cell_full_name(
    pacbio_barcoded_run_id: str, pacbio_barcoded_smrt_cell_name: str
) -> str:
    """Return the full name of a barcoded PacBio SMRT cell."""
    return f"{pacbio_barcoded_run_id}/{pacbio_barcoded_smrt_cell_name}"


@pytest.fixture
def pacbio_processed_smrt_cell_full_name(
    pacbio_barcoded_run_id: str, pac_bio_smrt_cell_name: str
) -> str:
    """Return the full name of a processed PacBio SMRT cell."""
    return f"{pacbio_barcoded_run_id}/{pac_bio_smrt_cell_name}"


@pytest.fixture
def pacbio_smrt_cell_full_names(
    pacbio_smrt_cell_full_name: str,
    pacbio_barcoded_smrt_cell_full_name: str,
    pacbio_processed_smrt_cell_full_name: str,
) -> set[str]:
    return {
        pacbio_smrt_cell_full_name,
        pacbio_barcoded_smrt_cell_full_name,
        pacbio_processed_smrt_cell_full_name,
    }


@pytest.fixture
def pacbio_barcoded_1_c01_movie_name() -> str:
    """Return the full name of a PacBio SMRT cell."""
    return "m84202_240913_162115_s3"


@pytest.fixture
def barcoded_smrt_cell_internal_id() -> str:
    return "EA114368"


@pytest.fixture
def pacbio_barcoded_sample_internal_id() -> str:
    return "Bio Sample 4"


@pytest.fixture
def pacbio_unassigned_sample_internal_id() -> str:
    return "No Name"


@pytest.fixture
def pacbio_run_name_to_fetch() -> str:
    return "run_to_fetch"


@pytest.fixture
def pacbio_run_name_not_to_fetch() -> str:
    return "run_not_to_fetch"
