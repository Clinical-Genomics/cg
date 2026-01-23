"""Module for the Pacbio database store service."""

import logging
from datetime import datetime

from cg.exc import PacbioSequencingRunAlreadyExistsError
from cg.services.run_devices.abstract_classes import PostProcessingStoreService
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import (
    PostProcessingDataTransferError,
    PostProcessingStoreDataError,
)
from cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
    PacBioSMRTCellMetricsDTO,
)
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.store.models import PacbioSequencingRun, PacbioSMRTCell, PacbioSMRTCellMetrics
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class PacBioStoreService(PostProcessingStoreService):
    def __init__(self, store: Store, data_transfer_service: PacBioDataTransferService):
        self.store = store
        self.data_transfer_service = data_transfer_service

    def _create_run_device(self, run_device_dto: PacBioSMRTCellDTO) -> PacbioSMRTCell:
        return self.store.create_pac_bio_smrt_cell(run_device_dto)

    def _create_pacbio_sequencing_run_if_non_existent(
        self, sequencing_run_dto: PacBioSequencingRunDTO
    ) -> PacbioSequencingRun:
        try:
            return self.store.create_pacbio_sequencing_run(sequencing_run_dto)
        except PacbioSequencingRunAlreadyExistsError:
            LOG.debug(f"Sequencing run {sequencing_run_dto.internal_id} already exists")
            return self.store.get_pacbio_sequencing_run_by_internal_id(
                sequencing_run_dto.internal_id
            )

    def _create_pacbio_smrt_cell_metrics(
        self,
        instrument_run_dto: PacBioSMRTCellMetricsDTO,
        sequencing_run: PacbioSequencingRun,
        smrt_cell: PacbioSMRTCell,
    ) -> PacbioSMRTCellMetrics:
        return self.store.create_pacbio_smrt_cell_metrics(
            smrt_cell_metrics_dto=instrument_run_dto,
            sequencing_run=sequencing_run,
            smrt_cell=smrt_cell,
        )

    def _create_sample_run_metrics(
        self,
        sample_run_metrics_dtos: list[PacBioSampleSequencingMetricsDTO],
        smrt_cell_metrics: PacbioSMRTCellMetrics,
    ) -> None:
        for sample_run_metric in sample_run_metrics_dtos:
            self.store.create_pac_bio_sample_sequencing_run(
                sample_run_metrics_dto=sample_run_metric, smrt_cell_metrics=smrt_cell_metrics
            )

    def _update_sample(
        self,
        sample_run_metrics_dtos: list[PacBioSampleSequencingMetricsDTO],
        sequencing_date: datetime,
    ) -> None:
        """Update the reads and last sequenced date for the SMRT cell samples."""
        sample_ids_to_update: set[str] = {
            sample_dto.sample_internal_id for sample_dto in sample_run_metrics_dtos
        }
        for sample_id in sample_ids_to_update:
            self.store.recalculate_sample_reads_pacbio(sample_id)
            self.store.update_sample_sequenced_at(internal_id=sample_id, date=sequencing_date)

    @handle_post_processing_errors(
        to_except=(PostProcessingDataTransferError, ValueError),
        to_raise=PostProcessingStoreDataError,
    )
    def store_post_processing_data(self, run_data: PacBioRunData, dry_run: bool = False) -> None:
        dtos: PacBioDTOs = self.data_transfer_service.get_post_processing_dtos(run_data)
        sequencing_run: PacbioSequencingRun = self._create_pacbio_sequencing_run_if_non_existent(
            dtos.sequencing_run
        )
        smrt_cell: PacbioSMRTCell = self._create_run_device(dtos.run_device)
        smrt_cell_metrics: PacbioSMRTCellMetrics = self._create_pacbio_smrt_cell_metrics(
            instrument_run_dto=dtos.smrt_cell_metrics,
            sequencing_run=sequencing_run,
            smrt_cell=smrt_cell,
        )
        self._create_sample_run_metrics(
            sample_run_metrics_dtos=dtos.sample_sequencing_metrics,
            smrt_cell_metrics=smrt_cell_metrics,
        )
        self._update_sample(
            sample_run_metrics_dtos=dtos.sample_sequencing_metrics,
            sequencing_date=smrt_cell_metrics.completed_at,
        )
        if dry_run:
            self.store.rollback()
            LOG.info(
                f"Dry run, no entries will be added to database for SMRT cell {run_data.full_path}."
            )
            return
        LOG.debug(f"Data stored in statusDB for run {run_data.run_internal_id}")
        self.store.commit_to_store()
