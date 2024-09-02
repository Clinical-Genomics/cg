from pathlib import Path
from unittest import mock

import pytest

from cg.services.run_devices.exc import PostProcessingRunFileManagerError
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager


def test_get_files_to_parse(
    expected_pac_bio_run_data: PacBioRunData,
    pac_bio_report_files_to_parse: list[Path],
    pac_bio_run_file_manager: PacBioRunFileManager,
):
    # GIVEN a run data object and a PacBio run file manager

    # WHEN getting the files to parse
    files: list[Path] = pac_bio_run_file_manager.get_files_to_parse(expected_pac_bio_run_data)

    # THEN the correct files are returned
    assert files == pac_bio_report_files_to_parse


def test_get_files_to_store(
    expected_pac_bio_run_data: PacBioRunData,
    pac_bio_run_file_manager: PacBioRunFileManager,
    pac_bio_report_files_to_parse: list[Path],
    pac_bio_hifi_read_file: Path,
):
    # GIVEN a run data object and a PacBio file manager

    # WHEN getting the files to store
    files: list[Path] = pac_bio_run_file_manager.get_files_to_store(expected_pac_bio_run_data)

    # THEN the correct files are returned
    full_list: list[Path] = pac_bio_report_files_to_parse + [pac_bio_hifi_read_file]
    assert set(files) == set(full_list)


def test_get_files_to_store_error(
    expected_pac_bio_run_data: PacBioRunData,
    pac_bio_run_file_manager: PacBioRunFileManager,
):
    # GIVEN a run data object

    # GIVEN a PacBio run file manager that can't find the HiFi read file
    with mock.patch.object(
        pac_bio_run_file_manager,
        attribute="_get_hifi_read_files",
        side_effect=FileNotFoundError,
    ):
        # WHEN getting the files to store

        # THEN an PostProcessingRunFileManagerError is raised
        with pytest.raises(PostProcessingRunFileManagerError):
            pac_bio_run_file_manager.get_files_to_store(expected_pac_bio_run_data)


def test_get_files_to_parse_error(
    expected_pac_bio_run_data: PacBioRunData,
    pac_bio_run_file_manager: PacBioRunFileManager,
):
    # GIVEN a run data object

    # GIVEN a PacBio run file manager that can't find the CCS report file
    with mock.patch.object(
        pac_bio_run_file_manager,
        attribute="_get_ccs_report_file",
        side_effect=FileNotFoundError,
    ):
        # WHEN getting the files to store

        # THEN an PostProcessingRunFileManagerError is raised
        with pytest.raises(PostProcessingRunFileManagerError):
            pac_bio_run_file_manager.get_files_to_parse(expected_pac_bio_run_data)
