"""Tests for the PacBioPostprocessingService."""

from unittest import mock
from unittest.mock import Mock

import pytest

from cg.models.cg_config import CGConfig
from cg.services.run_devices.exc import (
    PostProcessingError,
    PostProcessingRunFileManagerError,
    PostProcessingStoreDataError,
    PostProcessingStoreFileError,
)
from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService


def test_pac_bio_post_processing_run_name_error(pac_bio_context):
    # GIVEN a PacBioPostProcessingService and a wrong run name
    run_name: str = "run_name"
    post_processing_service: PacBioPostProcessingService = (
        pac_bio_context.post_processing_services.pacbio
    )

    # WHEN storing post-processing data

    # THEN a PostProcessingError is raised
    with pytest.raises(PostProcessingError):
        post_processing_service.post_process(run_name=run_name)


def test_pac_bio_post_processing_store_data_error(
    pac_bio_context: CGConfig, pacbio_barcoded_sequencing_run_name: str
):
    # GIVEN a PacBioPostProcessingService that raises an error when storing data in StatusDB

    post_processing_service: PacBioPostProcessingService = (
        pac_bio_context.post_processing_services.pacbio
    )

    # WHEN storing post-processing data raises an error
    with mock.patch.object(
        PacBioStoreService, "store_post_processing_data", side_effect=PostProcessingStoreDataError
    ):
        # THEN a PostProcessingError is raised
        with pytest.raises(PostProcessingError):
            post_processing_service.post_process(run_name=pacbio_barcoded_sequencing_run_name)


def test_pac_bio_post_processing_store_files_error(
    pac_bio_context: CGConfig, pacbio_barcoded_sequencing_run_name: str
):
    # GIVEN a PacBioPostProcessingService that raises an error when storing files in Housekeeper
    post_processing_service: PacBioPostProcessingService = (
        pac_bio_context.post_processing_services.pacbio
    )
    post_processing_service.store_service = Mock()

    # WHEN storing post-processing files raises an error
    with mock.patch.object(
        PacBioHousekeeperService,
        "store_files_in_housekeeper",
        side_effect=PostProcessingStoreFileError,
    ):
        # THEN a PostProcessingError is raised
        with pytest.raises(PostProcessingError):
            post_processing_service.post_process(run_name=pacbio_barcoded_sequencing_run_name)


def test_can_post_processing_start_true(
    pac_bio_post_processing_service: PacBioPostProcessingService,
    pacbio_barcoded_sequencing_run_name,
):
    """Tests that the post-processing is deemed ready to start when SMRT cells are ready."""
    # GIVEN a parent folder with two SMRT-cells

    # GIVEN both of them are ready for post-processing
    pac_bio_post_processing_service.run_validator.validate_run_files = Mock(
        side_effect=[None, None]
    )
    # WHEN checking if post-processing can start
    can_start: bool = pac_bio_post_processing_service.can_post_processing_start(
        pacbio_barcoded_sequencing_run_name
    )

    # THEN it should return True
    assert can_start


def test_can_post_processing_start_false(
    pac_bio_post_processing_service: PacBioPostProcessingService,
    pacbio_barcoded_sequencing_run_name,
):
    """Tests that the post-processing is not deemed ready to start when at least one SMRT cell is not are ready."""
    # GIVEN a parent folder with two SMRT-cells

    # GIVEN one of them is not ready for post-processing
    pac_bio_post_processing_service.run_validator.validate_run_files = Mock(
        side_effect=[
            None,
            PostProcessingRunFileManagerError(
                f"No Manifest file found in {pacbio_barcoded_sequencing_run_name}"
            ),
        ]
    )

    # WHEN checking if post-processing can start
    can_start: bool = pac_bio_post_processing_service.can_post_processing_start(
        pacbio_barcoded_sequencing_run_name
    )

    # THEN it should return False
    assert not can_start
