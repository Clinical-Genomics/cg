from pathlib import Path

from cg.models.run_devices.pacbio_cell_directory_data import PacBioCellDirectoryData


def test_pacbio_cell_directory_data(
    pac_bio_smrt_cell_dir_1_a01: Path, pac_bio_run_statistics_dir: Path
):
    """Test that a PacBioCellDirectoryData object is created with the correct attributes."""
    # GIVEN a path to a PacBio SMRT cell directory

    # WHEN creating a PacBioCellDirectoryData object
    pac_bio_cell_directory_data: PacBioCellDirectoryData = PacBioCellDirectoryData(
        pac_bio_smrt_cell_dir_1_a01
    )

    # THEN the object is created with the correct attributes
    assert pac_bio_cell_directory_data.path == pac_bio_smrt_cell_dir_1_a01
    assert pac_bio_cell_directory_data.statistics_dir == pac_bio_run_statistics_dir


def test_ccs_report(
    pac_bio_cell_directory_data_1_a01: PacBioCellDirectoryData, ccs_report_1_a01_name: str
):
    """Test that the correct ccs report file is returned."""
    # GIVEN a PacBioCellDirectoryData object

    # WHEN accessing the ccs_report property
    ccs_report: Path = pac_bio_cell_directory_data_1_a01.ccs_report

    # THEN the correct ccs report file is returned
    assert ccs_report.name == ccs_report_1_a01_name
    assert ccs_report.exists()
