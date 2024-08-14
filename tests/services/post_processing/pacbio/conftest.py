"""Fixtures for the PacBio post processing services."""

from pathlib import Path

import pytest

from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData


@pytest.fixture
def expected_pac_bio_run_data(
    pac_bio_test_run_name: str, pac_bio_smrt_cell_dir_1_a01: Path
) -> PacBioRunData:
    return PacBioRunData(
        full_path=pac_bio_smrt_cell_dir_1_a01,
        sequencing_run_name=pac_bio_test_run_name,
        well_name="A01",
        plate=1,
    )
