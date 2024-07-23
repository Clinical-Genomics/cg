from pathlib import Path

import pytest

from cg.models.run_devices.pacbio_cell_directory_data import PacBioCellDirectoryData


@pytest.fixture
def pac_bio_cell_directory_data_1_a01(pac_bio_smrt_cell_dir_1_a01: Path) -> PacBioCellDirectoryData:
    """Return the PacBioCellDirectoryData for the 1_A01 SMRT cell."""
    return PacBioCellDirectoryData(pac_bio_smrt_cell_dir_1_a01)
