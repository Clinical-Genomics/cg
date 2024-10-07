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
from cg.store.models import (
    PacbioSampleSequencingMetrics,
    PacbioSequencingRun,
    PacbioSMRTCell,
    Sample,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_store_post_processing_data(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_run_data: PacBioRunData,
    helpers: StoreHelpers,
):
    # GIVEN a PacBioStoreService and a data transfer service

    # GIVEN that the store has a sample
    helpers.add_sample(
        store=pac_bio_store_service.store,
        internal_id=pac_bio_dtos.sample_sequencing_metrics[0].sample_internal_id,
    )

    # GIVEN that the store has no sequencing data
    assert not pac_bio_store_service.store._get_query(PacbioSampleSequencingMetrics).first()
    assert not pac_bio_store_service.store._get_query(PacbioSequencingRun).first()
    assert not pac_bio_store_service.store._get_query(PacbioSMRTCell).first()

    # GIVEN a data transfer service that returns the correct DTOs

    # WHEN storing data for a PacBio instrument run
    with mock.patch(
        "cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service.PacBioDataTransferService.get_post_processing_dtos",
        return_value=pac_bio_dtos,
    ):
        pac_bio_store_service.store_post_processing_data(pacbio_barcoded_run_data)

    # THEN the SMRT cell data is stored with the correct data
    smrt_cell: PacbioSMRTCell = pac_bio_store_service.store._get_query(PacbioSMRTCell).first()
    assert smrt_cell
    assert smrt_cell.internal_id == pac_bio_dtos.run_device.internal_id

    # THEN the sequencing run is stored with the correct data
    sequencing_run: PacbioSequencingRun = pac_bio_store_service.store._get_query(
        PacbioSequencingRun
    ).first()
    assert sequencing_run
    assert sequencing_run.well == pac_bio_dtos.sequencing_run.well

    # THEN the sample sequencing metrics are stored with the correct data
    sample_sequencing_run_metrics: list[PacbioSampleSequencingMetrics] = (
        pac_bio_store_service.store._get_query(PacbioSampleSequencingMetrics).all()
    )
    assert sample_sequencing_run_metrics
    for sample_metrics in sample_sequencing_run_metrics:
        assert (
            sample_metrics.sample.internal_id
            == pac_bio_dtos.sample_sequencing_metrics[0].sample_internal_id
        )

    # THEN the sample reads and sequenced date are updated
    for sample_metrics_dto in pac_bio_dtos.sample_sequencing_metrics:
        sample: Sample = pac_bio_store_service.store.get_sample_by_internal_id(
            sample_metrics_dto.sample_internal_id
        )
        assert sample
        assert sample.reads == sample_metrics_dto.hifi_reads
        assert sample.last_sequenced_at == pac_bio_dtos.sequencing_run.completed_at


def test_store_post_processing_data_error_database(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_run_data: PacBioRunData,
):
    # GIVEN a PacbioStoreService and a Pacbio run data object

    # GIVEN a store that raises an error when creating a PacBio SMRT cell

    # WHEN trying to store data for a Pacbio instrument run
    with mock.patch(
        "cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service.PacBioDataTransferService.get_post_processing_dtos",
        return_value=pac_bio_dtos,
    ), mock.patch.object(Store, "create_pac_bio_smrt_cell", side_effect=ValueError):
        # THEN a PostProcessingStoreDataError is raised
        with pytest.raises(PostProcessingStoreDataError):
            pac_bio_store_service.store_post_processing_data(pacbio_barcoded_run_data)


def test_store_post_processing_data_error_parser(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_run_data: PacBioRunData,
):
    # GIVEN a PacbioStoreService and a Pacbio run data object

    # GIVEN a data transfer service that raises an error when parsing data

    # WHEN trying to store data for a PacBio instrument ru
    with mock.patch(
        "cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service.PacBioDataTransferService.get_post_processing_dtos",
        return_value=pac_bio_dtos,
    ), mock.patch.object(
        PacBioDataTransferService,
        "get_post_processing_dtos",
        side_effect=PostProcessingDataTransferError,
    ):
        # THEN a PostProcessingStoreDataError is raised
        with pytest.raises(PostProcessingStoreDataError):
            pac_bio_store_service.store_post_processing_data(pacbio_barcoded_run_data)
