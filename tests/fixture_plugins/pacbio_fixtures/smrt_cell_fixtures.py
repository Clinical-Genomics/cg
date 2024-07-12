from pathlib import Path

import pytest

from cg.models.run_devices.pac_bio_smrt_cell import PacBioRunDirectoryData


@pytest.fixture
def pac_bio_smrt_cell(pac_bio_smrt_cell_dir: Path) -> PacBioRunDirectoryData:
    """Returns a PacBio directory data object"""
    return PacBioRunDirectoryData(pac_bio_smrt_cell_dir)
