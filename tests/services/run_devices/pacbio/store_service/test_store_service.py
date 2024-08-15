"""Module to test the PacBioStoreService."""

from unittest import mock

import pytest

from cg.services.run_devices.exc import (
    PostProcessingDataTransferError,
    PostProcessingStoreDataError,
)
from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioDTOs
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.store.models import PacBioSampleSequencingMetrics, PacBioSequencingRun, PacBioSMRTCell
from cg.store.store import Store


def test_store_post_processing_data(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    expected_pac_bio_run_data: PacBioRunData,
):
    # GIVEN a PacBioStoreService

    # GIVEN a data transfer service that returns the correct DTOs

    # WHEN storing data for a PacBio instrument run
    with mock.patch(
        "cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service.PacBioDataTransferService.get_post_processing_dtos",
        return_value=pac_bio_dtos,
    ):
        pac_bio_store_service.store_post_processing_data(expected_pac_bio_run_data)

    # THEN the SMRT cell data is stored
    smrt_cell: PacBioSMRTCell = pac_bio_store_service.store._get_query(PacBioSMRTCell).first()
    assert smrt_cell
    assert smrt_cell.internal_id == pac_bio_dtos.run_device.internal_id

    # THEN the sequencing run is stored
    sequencing_run: PacBioSequencingRun = pac_bio_store_service.store._get_query(
        PacBioSequencingRun
    ).first()
    assert sequencing_run
    assert sequencing_run.well == pac_bio_dtos.sequencing_run.well

    # THEN the sample sequencing metrics are stored
    sample_sequencing_run_metrics: PacBioSampleSequencingMetrics = (
        pac_bio_store_service.store._get_query(PacBioSampleSequencingMetrics).first()
    )
    assert sample_sequencing_run_metrics
    assert (
        sample_sequencing_run_metrics.sample.internal_id
        == pac_bio_dtos.sample_sequencing_metrics[0].sample_internal_id
    )


def test_store_post_processing_data_error_database(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    expected_pac_bio_run_data: PacBioRunData,
):
    # GIVEN a PacBioStoreService

    # GIVEN a data transfer service that returns the correct DTOs

    # WHEN storing data for a PacBio instrument run
    with mock.patch(
        "cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service.PacBioDataTransferService.get_post_processing_dtos",
        return_value=pac_bio_dtos,
    ), mock.patch.object(Store, "create_pac_bio_smrt_cell", side_effect=ValueError):
        with pytest.raises(PostProcessingStoreDataError):
            pac_bio_store_service.store_post_processing_data(expected_pac_bio_run_data)


def test_store_post_processing_data_error_parser(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    expected_pac_bio_run_data: PacBioRunData,
):
    # GIVEN a PacBioStoreService

    # GIVEN a data transfer service that returns the correct DTOs

    # WHEN storing data for a PacBio instrument run
    with mock.patch(
        "cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service.PacBioDataTransferService.get_post_processing_dtos",
        return_value=pac_bio_dtos,
    ), mock.patch.object(
        PacBioDataTransferService,
        "get_post_processing_dtos",
        side_effect=PostProcessingDataTransferError,
    ):
        with pytest.raises(PostProcessingStoreDataError):
            pac_bio_store_service.store_post_processing_data(expected_pac_bio_run_data)
