from pathlib import Path

import pytest

from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.constants.pacbio import PacBioHousekeeperTags
from cg.services.run_devices.pacbio.housekeeper_service.models import PacBioFileData


@pytest.fixture
def ccs_report_pac_bio_file_data(
    pac_bio_ccs_report_file: Path, smrt_cell_internal_id: str
) -> PacBioFileData:
    """Return a PacBioFileData object for a CCS report file."""
    return PacBioFileData(
        file_path=pac_bio_ccs_report_file,
        bundle_name=smrt_cell_internal_id,
        tags=[PacBioHousekeeperTags.CCS_REPORT, smrt_cell_internal_id],
    )


@pytest.fixture
def pac_bio_hifi_reads_file_data(
    pac_bio_hifi_read_file: Path, smrt_cell_internal_id: str, pac_bio_sample_internal_id: str
) -> PacBioFileData:
    """Return a PacBioFileData object for a HiFi reads file."""
    return PacBioFileData(
        file_path=pac_bio_hifi_read_file,
        bundle_name=pac_bio_sample_internal_id,
        tags=[AlignmentFileTag.BAM, smrt_cell_internal_id, pac_bio_sample_internal_id],
    )
