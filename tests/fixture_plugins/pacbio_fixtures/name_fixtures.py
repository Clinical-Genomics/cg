"""Module for PacBio fixtures returning strings."""

import pytest


@pytest.fixture
def pac_bio_smrt_cell_name() -> str:
    return "1_B01"


@pytest.fixture
def pacbio_barcoded_smrt_cell_name() -> str:
    return "1_C01"


@pytest.fixture
def pac_bio_test_run_name() -> str:
    """Return the name of a PacBio SMRT cell."""
    return "r84202_20240522_133539"


@pytest.fixture
def pacbio_barcoded_run_name() -> str:
    return "r84202_20240913_121403"


@pytest.fixture
def pacbio_sequencing_run_name(pac_bio_test_run_name: str, pac_bio_smrt_cell_name: str) -> str:
    """Return the name of a PacBio SMRT cell."""
    return f"{pac_bio_test_run_name}/{pac_bio_smrt_cell_name}"


@pytest.fixture
def pacbio_barcoded_sequencing_run_name(
    pacbio_barcoded_run_name: str, pacbio_barcoded_smrt_cell_name: str
) -> str:
    """Return the name of a PacBio SMRT cell."""
    return f"{pacbio_barcoded_run_name}/{pacbio_barcoded_smrt_cell_name}"


@pytest.fixture
def pacbio_processed_sequencing_run_name(
    pacbio_barcoded_run_name: str, pac_bio_smrt_cell_name: str
) -> str:
    """Return the name of a PacBio SMRT cell."""
    return f"{pacbio_barcoded_run_name}/{pac_bio_smrt_cell_name}"


@pytest.fixture
def pacbio_run_names(
    pacbio_sequencing_run_name: str,
    pacbio_barcoded_sequencing_run_name: str,
    pacbio_processed_sequencing_run_name: str,
) -> set[str]:
    return {
        pacbio_sequencing_run_name,
        pacbio_barcoded_sequencing_run_name,
        pacbio_processed_sequencing_run_name,
    }


@pytest.fixture
def pacbio_barcoded_1_c01_cell_full_name() -> str:
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
