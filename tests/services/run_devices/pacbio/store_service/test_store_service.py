"""Module to test the PacBioStoreService."""

from datetime import timezone

import pytest
from pytest_mock import MockerFixture

from cg.constants.devices import RevioNames
from cg.exc import PacbioSequencingRunAlreadyExistsError
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
    PacbioSMRTCellMetrics,
    Sample,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_store_post_processing_data(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_run_data: PacBioRunData,
    pacbio_barcoded_run_id: str,
    helpers: StoreHelpers,
    mocker: MockerFixture,
):
    # GIVEN a PacBioStoreService and a data transfer service

    # GIVEN that the store has a sample
    helpers.add_sample(
        store=pac_bio_store_service.store,
        internal_id=pac_bio_dtos.sample_sequencing_metrics[0].sample_internal_id,
    )

    # GIVEN that the store has no sequencing data
    assert not pac_bio_store_service.store._get_query(PacbioSampleSequencingMetrics).first()
    assert not pac_bio_store_service.store._get_query(PacbioSMRTCellMetrics).first()
    assert not pac_bio_store_service.store._get_query(PacbioSMRTCell).first()
    assert not pac_bio_store_service.store._get_query(PacbioSequencingRun).first()

    # GIVEN a data transfer service that returns the correct DTOs
    mocker.patch.object(
        PacBioDataTransferService, "get_post_processing_dtos", return_value=pac_bio_dtos
    )

    # WHEN storing data for a PacBio instrument run
    pac_bio_store_service.store_post_processing_data(pacbio_barcoded_run_data)

    # THEN the SMRT cell data is stored with the correct data
    smrt_cell: PacbioSMRTCell = pac_bio_store_service.store._get_query(PacbioSMRTCell).first()
    assert smrt_cell
    assert smrt_cell.internal_id == pac_bio_dtos.run_device.internal_id

    # THEN the SMRT cell metrics are stored with the correct data
    smrt_cell_metrics: PacbioSMRTCellMetrics = pac_bio_store_service.store._get_query(
        PacbioSMRTCellMetrics
    ).first()
    assert smrt_cell_metrics
    assert smrt_cell_metrics.well == pac_bio_dtos.smrt_cell_metrics.well

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

    # THEN a PacbioSequencingRun is stored with the correct data
    pacbio_sequencing_run: PacbioSequencingRun = pac_bio_store_service.store._get_query(
        PacbioSequencingRun
    ).one()
    assert pacbio_sequencing_run.run_id == pacbio_barcoded_run_id
    assert pacbio_sequencing_run.instrument_name == RevioNames.WILMA
    assert pacbio_sequencing_run.run_name == "run-name"
    assert pacbio_sequencing_run.unique_id == "unique-id"

    # THEN the sample reads and sequenced date are updated
    for sample_metrics_dto in pac_bio_dtos.sample_sequencing_metrics:
        sample: Sample = pac_bio_store_service.store.get_sample_by_internal_id(
            sample_metrics_dto.sample_internal_id
        )
        assert sample
        assert sample.reads == sample_metrics_dto.hifi_reads
        assert (
            sample.last_sequenced_at.replace(tzinfo=timezone.utc)
            == pac_bio_dtos.smrt_cell_metrics.completed_at
        )


def test_store_post_processing_data_error_database(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_run_data: PacBioRunData,
    mocker: MockerFixture,
):
    # GIVEN a PacbioStoreService and a Pacbio run data object

    # GIVEN a store that raises an error when creating a PacBio SMRT cell

    # WHEN trying to store data for a Pacbio instrument run
    mocker.patch.object(
        PacBioDataTransferService, "get_post_processing_dtos", return_value=pac_bio_dtos
    )
    mocker.patch.object(Store, "create_pac_bio_smrt_cell", side_effect=ValueError)

    # THEN a PostProcessingStoreDataError is raised
    with pytest.raises(PostProcessingStoreDataError):
        pac_bio_store_service.store_post_processing_data(pacbio_barcoded_run_data)


def test_store_post_processing_data_error_parser(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_run_data: PacBioRunData,
    mocker: MockerFixture,
):
    # GIVEN a PacbioStoreService and a Pacbio run data object

    # GIVEN a data transfer service that raises an error when parsing data

    # WHEN trying to store data for a PacBio instrument ru
    mocker.patch.object(
        PacBioDataTransferService, "get_post_processing_dtos", return_value=pac_bio_dtos
    )
    mocker.patch.object(
        PacBioDataTransferService,
        "get_post_processing_dtos",
        side_effect=PostProcessingDataTransferError,
    )

    # THEN a PostProcessingStoreDataError is raised
    with pytest.raises(PostProcessingStoreDataError):
        pac_bio_store_service.store_post_processing_data(pacbio_barcoded_run_data)


def test_store_post_processing_multiple_smrt_cells(
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_run_data: PacBioRunData,
    helpers: StoreHelpers,
    mocker: MockerFixture,
):
    # GIVEN a PacBioStoreService and a data transfer service

    # GIVEN that the store has a sample
    helpers.add_sample(
        store=pac_bio_store_service.store,
        internal_id=pac_bio_dtos.sample_sequencing_metrics[0].sample_internal_id,
    )

    # GIVEN that the store already has a PacBio sequencing run with the same run name
    pac_bio_store_service.store.create_pacbio_sequencing_run(pac_bio_dtos.sequencing_run)
    pac_bio_store_service.store.commit_to_store()

    # WHEN creating PacBio sequencing run with the run name
    mocker.patch.object(
        PacBioDataTransferService, "get_post_processing_dtos", return_value=pac_bio_dtos
    )
    already_exists_spy = mocker.spy(PacbioSequencingRunAlreadyExistsError, "__init__")
    pac_bio_store_service.store_post_processing_data(run_data=pacbio_barcoded_run_data)

    # THEN no additional PacBio sequencing run should be added
    sequencing_runs: list[PacbioSequencingRun] = pac_bio_store_service.store._get_query(
        PacbioSequencingRun
    ).all()
    assert len(sequencing_runs) == 1
    already_exists_spy.assert_called()
