from pathlib import Path

import pytest

from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.constants.pacbio import PacBioHousekeeperTags
from cg.services.run_devices.pacbio.housekeeper_service.models import PacBioFileData


@pytest.fixture
def ccs_report_pac_bio_file_data(
    pacbio_barcoded_ccs_report_file: Path, barcoded_smrt_cell_internal_id: str
) -> PacBioFileData:
    """Return a PacBioFileData object for a CCS report file."""
    return PacBioFileData(
        file_path=pacbio_barcoded_ccs_report_file,
        bundle_name=barcoded_smrt_cell_internal_id,
        tags=[PacBioHousekeeperTags.CCS_REPORT, barcoded_smrt_cell_internal_id],
    )


@pytest.fixture
def pac_bio_hifi_reads_file_data(
    pacbio_barcoded_hifi_read_file: Path,
    barcoded_smrt_cell_internal_id: str,
    pacbio_barcoded_sample_internal_id: str,
) -> PacBioFileData:
    """Return a PacBioFileData object for a HiFi reads file."""
    return PacBioFileData(
        file_path=pacbio_barcoded_hifi_read_file,
        bundle_name=pacbio_barcoded_sample_internal_id,
        tags=[
            AlignmentFileTag.BAM,
            barcoded_smrt_cell_internal_id,
            pacbio_barcoded_sample_internal_id,
        ],
    )
