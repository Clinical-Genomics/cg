"""PacBio run data object fixtures."""

from pathlib import Path

import pytest

from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData


@pytest.fixture
def expected_pac_bio_run_data_1_b01(
    pac_bio_test_run_name: str, pac_bio_smrt_cell_dir_1_b01: Path
) -> PacBioRunData:
    return PacBioRunData(
        full_path=pac_bio_smrt_cell_dir_1_b01,
        sequencing_run_name=pac_bio_test_run_name,
        well_name="B01",
        plate=1,
    )


@pytest.fixture
def pacbio_barcoded_run_data(
    pacbio_barcoded_run_name: str, pacbio_barcoded_smrt_cell_dir_1_c01: Path
) -> PacBioRunData:
    return PacBioRunData(
        full_path=pacbio_barcoded_smrt_cell_dir_1_c01,
        sequencing_run_name=pacbio_barcoded_run_name,
        well_name="C01",
        plate=1,
    )
