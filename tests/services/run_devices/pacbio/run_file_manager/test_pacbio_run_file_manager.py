from pathlib import Path
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from cg.services.run_devices.exc import PostProcessingRunFileManagerError
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager import run_file_manager
from cg.services.run_devices.pacbio.run_file_manager.models import PacBioRunValidatorFiles
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager


def test_get_files_to_parse(
    pacbio_barcoded_run_data: PacBioRunData,
    pacbio_barcoded_report_files_to_parse: list[Path],
    pac_bio_run_file_manager: PacBioRunFileManager,
):
    # GIVEN a run data object and a PacBio run file manager

    # WHEN getting the files to parse
    files: list[Path] = pac_bio_run_file_manager.get_files_to_parse(pacbio_barcoded_run_data)

    # THEN the correct files are returned
    assert files == pacbio_barcoded_report_files_to_parse


def test_get_files_to_store(
    pacbio_barcoded_run_data: PacBioRunData,
    pac_bio_run_file_manager: PacBioRunFileManager,
    pacbio_barcoded_report_files_to_parse: list[Path],
    pacbio_barcoded_hifi_read_files: list[Path],
):
    # GIVEN a run data object and a PacBio file manager

    # WHEN getting the files to store
    files: list[Path] = pac_bio_run_file_manager.get_files_to_store(pacbio_barcoded_run_data)

    # THEN the correct files are returned
    full_list: list[Path] = pacbio_barcoded_report_files_to_parse + pacbio_barcoded_hifi_read_files
    assert set(files) == set(full_list)


def test_get_files_to_store_error(
    pacbio_barcoded_run_data: PacBioRunData,
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
            pac_bio_run_file_manager.get_files_to_store(pacbio_barcoded_run_data)


def test_get_files_to_parse_error(
    pacbio_barcoded_run_data: PacBioRunData,
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
            pac_bio_run_file_manager.get_files_to_parse(pacbio_barcoded_run_data)


def test_get_run_validator_files_success(
    expected_pac_bio_run_data_1_b01, pac_bio_run_file_manager, expected_1_b01_run_validation_files
):
    # GIVEN a run data object

    # WHEN getting the run validation file paths
    validation_file_paths: PacBioRunValidatorFiles = (
        pac_bio_run_file_manager.get_run_validation_files(expected_pac_bio_run_data_1_b01)
    )

    # THEN the correct paths are returned
    assert validation_file_paths == expected_1_b01_run_validation_files


def test_get_run_validator_files_fail(
    tmp_path: Path,
    pac_bio_run_file_manager: PacBioRunFileManager,
    expected_1_b01_run_validation_files: PacBioRunValidatorFiles,
    mocker: MockerFixture,
):
    # GIVEN a run data object with a missing zipped reports
    pacbio_run_data = PacBioRunData(
        full_path=tmp_path / "run_name" / "1_B01",
        sequencing_run_name="run_name",
        well_name="1_B01",
        plate=1,
    )

    # GIVEN that no zipped nor unzipped reports file is found
    mocker.patch.object(
        run_file_manager, "get_files_matching_pattern", side_effect=[[Path("some", "file")], [], []]
    )

    # WHEN getting the run validation file paths
    # THEN a file not found exception is raised
    with pytest.raises(PostProcessingRunFileManagerError):
        pac_bio_run_file_manager.get_run_validation_files(pacbio_run_data)
