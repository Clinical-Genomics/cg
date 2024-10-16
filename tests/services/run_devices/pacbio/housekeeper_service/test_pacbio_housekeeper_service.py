"""Module for the PacBioHousekeeperService tests."""

from pathlib import Path
from unittest import mock

import pytest
from housekeeper.store.models import File

from cg.services.run_devices.exc import (
    PostProcessingParsingError,
    PostProcessingRunFileManagerError,
    PostProcessingStoreFileError,
)
from cg.services.run_devices.pacbio.housekeeper_service.models import PacBioFileData
from cg.services.run_devices.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.run_devices.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.run_devices.pacbio.metrics_parser.models import PacBioMetrics
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager


def test_store_files_in_housekeeper(
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    pacbio_barcoded_run_data: PacBioRunData,
    pacbio_barcoded_sample_internal_id: str,
    barcoded_smrt_cell_internal_id: str,
):
    # GIVEN a PacBioRunData object and a PacBioHousekeeperService

    # WHEN storing files in Housekeeper
    pac_bio_housekeeper_service.store_files_in_housekeeper(pacbio_barcoded_run_data)

    # THEN a SMRT cell bundle is created
    assert pac_bio_housekeeper_service.hk_api.get_latest_bundle_version(
        barcoded_smrt_cell_internal_id
    )

    # THEN a sample bundle is created
    assert pac_bio_housekeeper_service.hk_api.get_latest_bundle_version(
        pacbio_barcoded_sample_internal_id
    )

    # THEN all expected files are listed under the smrt cell bundle
    smrt_bundle_files: list[File] = (
        pac_bio_housekeeper_service.hk_api.get_files_from_latest_version(
            bundle_name=barcoded_smrt_cell_internal_id
        )
    )
    assert smrt_bundle_files

    # THEN all expected files are listed under the sample bundle
    sample_bundle_files: list[File] = pac_bio_housekeeper_service.hk_api.get_latest_bundle_version(
        bundle_name=pacbio_barcoded_sample_internal_id
    ).files
    assert sample_bundle_files


@pytest.mark.parametrize(
    "file_fixture, file_data_fixture",
    [
        ("pacbio_barcoded_ccs_report_file", "ccs_report_pac_bio_file_data"),
        ("pacbio_barcoded_hifi_read_file", "pac_bio_hifi_reads_file_data"),
    ],
    ids=["ccs_report", "hifi_reads"],
)
def test_create_bundle_info(
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    pac_bio_metrics: PacBioMetrics,
    file_fixture: str,
    file_data_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test the correct file data object is created for a file."""
    # GIVEN a PacBioMetrics and a Housekeeper PacBioHousekeeperService objects

    # GIVEN a file path
    file: Path = request.getfixturevalue(file_fixture)

    # WHEN creating the file data object for the file
    file_data: PacBioFileData = pac_bio_housekeeper_service._create_bundle_info(
        file_path=file, parsed_metrics=pac_bio_metrics
    )

    # THEN the method should return the correct PacBioFileData object
    expected_file_data: PacBioFileData = request.getfixturevalue(file_data_fixture)
    assert file_data == expected_file_data


def test_create_bundle_info_unassigned_file(
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    pac_bio_metrics: PacBioMetrics,
    pacbio_unassigned_hifi_read_file: Path,
):
    """Test that getting the bundle of an unassigned file fails."""
    # GIVEN a PacBioMetrics and a Housekeeper PacBioHousekeeperService objects

    # GIVEN an unassigned reads file

    # WHEN creating the file data object for the file
    with pytest.raises(PostProcessingStoreFileError):
        # THEN the method raises a PostProcessingStoreFileError
        pac_bio_housekeeper_service._create_bundle_info(
            file_path=pacbio_unassigned_hifi_read_file, parsed_metrics=pac_bio_metrics
        )


def test_store_housekeeper_file_not_found(
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    pacbio_barcoded_run_data: PacBioRunData,
):
    # GIVEN a PacBioRunData object and a PacBioHousekeeperService

    # GIVEN a PacBioRunFileManager that raises an error when trying to get files to store

    # WHEN trying to store files in Housekeeper
    with mock.patch.object(
        PacBioRunFileManager, "get_files_to_store", side_effect=PostProcessingRunFileManagerError
    ):
        # THEN a PostProcessingRunFileManagerError is raised
        with pytest.raises(PostProcessingStoreFileError):
            pac_bio_housekeeper_service.store_files_in_housekeeper(pacbio_barcoded_run_data)


def test_store_housekeeper_parsing_error(
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    pacbio_barcoded_run_data: PacBioRunData,
):
    # GIVEN a PacBioRunData object and a PacBioHousekeeperService

    # GIVEN a Pacbio metrics parser that raises an error when parsing metrics

    # WHEN storing files in Housekeeper
    with mock.patch.object(
        PacBioMetricsParser, "parse_metrics", side_effect=PostProcessingParsingError
    ):
        # THEN an error is raised
        with pytest.raises(PostProcessingStoreFileError):
            pac_bio_housekeeper_service.store_files_in_housekeeper(pacbio_barcoded_run_data)


def test_get_sample_internal_id_from_file(
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    pacbio_barcoded_hifi_read_file: Path,
    pac_bio_metrics: PacBioMetrics,
    pacbio_barcoded_sample_internal_id: str,
):
    """Test that the sample internal ID can be extracted from a file."""
    # GIVEN a PacBio HiFi read file and a PacBioMetrics object

    # WHEN getting the sample internal ID from the file
    sample_internal_id: str = pac_bio_housekeeper_service._get_sample_internal_id_from_file(
        file_path=pacbio_barcoded_hifi_read_file, parsed_metrics=pac_bio_metrics
    )

    # THEN the sample internal ID should be returned
    assert sample_internal_id == pacbio_barcoded_sample_internal_id
