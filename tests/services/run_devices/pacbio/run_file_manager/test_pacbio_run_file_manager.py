from unittest import mock

import pytest
from pathlib import Path

from cg.services.run_devices.exc import PostProcessingRunFileManagerError
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
)


def test_get_files_to_parse(
    expected_pac_bio_run_data: PacBioRunData, pac_bio_report_files_to_parse: list[Path]
):
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
    pac_bio_hifi_read_file: Path,
):
    # GIVEN a run data object

    # GIVEN a PacBio run file manager
    file_manager = PacBioRunFileManager()

    # WHEN getting the files to store
    files: list[Path] = file_manager.get_files_to_store(expected_pac_bio_run_data)

    # THEN the correct files are returned
    full_list: list[Path] = pac_bio_report_files_to_parse + [pac_bio_hifi_read_file]
    assert set(files) == set(full_list)


def test_get_files_to_store_error(
    expected_pac_bio_run_data: PacBioRunData,
):
    # GIVEN a run data object

    # GIVEN a PacBio run file manager
    file_manager = PacBioRunFileManager()
    with mock.patch.object(
        file_manager,
        attribute="_get_hifi_read_file",
        side_effect=FileNotFoundError,
    ):
        # WHEN getting the files to store

        # THEN an PostProcessingRunFileManagerError is raised
        with pytest.raises(PostProcessingRunFileManagerError):
            file_manager.get_files_to_store(expected_pac_bio_run_data)


def test_get_files_to_parse_error(
    expected_pac_bio_run_data: PacBioRunData,
):
    # GIVEN a run data object

    # GIVEN a PacBio run file manager
    file_manager = PacBioRunFileManager()
    with mock.patch.object(
        file_manager,
        attribute="_get_ccs_report_file",
        side_effect=FileNotFoundError,
    ):
        # WHEN getting the files to store

        # THEN an PostProcessingRunFileManagerError is raised
        with pytest.raises(PostProcessingRunFileManagerError):
            file_manager.get_files_to_parse(expected_pac_bio_run_data)
