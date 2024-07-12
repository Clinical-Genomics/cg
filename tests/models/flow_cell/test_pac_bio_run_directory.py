from pathlib import Path

from cg.constants import FileExtensions
from cg.models.run_devices.pac_bio_smrt_cell import PacBioRunDirectoryData


def test_get_report_zip_file(pac_bio_smrt_cell: PacBioRunDirectoryData):
    """Test that a report zip file is returned correctly"""
    # GIVEN a PacBio run directory data with a reports.zip file

    # WHEN getting the reports.zip file
    zip_file: Path = pac_bio_smrt_cell.get_report_zip_file()

    # THEN the file exists and teh path has the correct extension
    assert zip_file
    assert zip_file.suffix == FileExtensions.ZIP
