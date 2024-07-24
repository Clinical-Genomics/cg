from pathlib import Path

from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.post_processing.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
)


def test_get_files_to_parse(
    expected_pac_bio_run_data: PacBioRunData, pac_bio_report_files_to_parse: list[Path]
):
    """Test that the report file paths are returned."""

    # GIVEN a run data object

    # GIVEN a PacBio run file manager
    file_manager = PacBioRunFileManager()

    # WHEN getting the files to parse
    files: list[Path] = file_manager.get_files_to_parse(expected_pac_bio_run_data)

    # THEN the correct files are returned
    assert files == pac_bio_report_files_to_parse


def test_get_files_to_store(
    expected_pac_bio_run_data: PacBioRunData,
    pac_bio_report_files_to_parse: list[Path],
    pac_bio_hifi_files: list[Path],
):
    """Test that the files to be stored are returned"""

    # GIVEN a run data object

    # GIVEN a PacBio run file manager
    file_manager = PacBioRunFileManager()

    # WHEN getting the files to store
    files: list[Path] = file_manager.get_files_to_store(expected_pac_bio_run_data)

    # THEN the correct files are returned
    full_list: list[Path] = pac_bio_report_files_to_parse + pac_bio_hifi_files
    assert set(files) == set(full_list)
