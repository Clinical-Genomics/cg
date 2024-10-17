"""Module for the Pacbio database store service."""

import logging
from datetime import datetime

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
)
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.store.models import PacbioSequencingRun, PacbioSMRTCell
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class PacBioStoreService(PostProcessingStoreService):
    def __init__(self, store: Store, data_transfer_service: PacBioDataTransferService):
        self.store = store
        self.data_transfer_service = data_transfer_service

    def _create_run_device(self, run_device_dto: PacBioSMRTCellDTO) -> PacbioSMRTCell:
        return self.store.create_pac_bio_smrt_cell(run_device_dto)

    def _create_instrument_run(
        self, instrument_run_dto: PacBioSequencingRunDTO, smrt_cell: PacbioSMRTCell
    ) -> PacbioSequencingRun:
        return self.store.create_pac_bio_sequencing_run(
            sequencing_run_dto=instrument_run_dto, smrt_cell=smrt_cell
        )

    def _create_sample_run_metrics(
        self,
        sample_run_metrics_dtos: list[PacBioSampleSequencingMetricsDTO],
        sequencing_run: PacbioSequencingRun,
    ) -> None:
        for sample_run_metric in sample_run_metrics_dtos:
            self.store.create_pac_bio_sample_sequencing_run(
                sample_run_metrics_dto=sample_run_metric, sequencing_run=sequencing_run
            )

    def _update_sample(
        self,
        sample_run_metrics_dtos: list[PacBioSampleSequencingMetricsDTO],
        sequencing_date: datetime,
    ) -> None:
        """Update the reads and last sequenced date for the SMRT cell samples."""
        for sample_dto in sample_run_metrics_dtos:
            self.store.update_sample_reads(
                internal_id=sample_dto.sample_internal_id, reads=sample_dto.hifi_reads
            )
            self.store.update_sample_sequenced_at(
                internal_id=sample_dto.sample_internal_id, date=sequencing_date
            )

    @handle_post_processing_errors(
        to_except=(PostProcessingDataTransferError, ValueError),
        to_raise=PostProcessingStoreDataError,
    )
    def store_post_processing_data(self, run_data: PacBioRunData, dry_run: bool = False) -> None:
        dtos: PacBioDTOs = self.data_transfer_service.get_post_processing_dtos(run_data)
        smrt_cell: PacbioSMRTCell = self._create_run_device(dtos.run_device)
        sequencing_run: PacbioSequencingRun = self._create_instrument_run(
            instrument_run_dto=dtos.sequencing_run, smrt_cell=smrt_cell
        )
        self._create_sample_run_metrics(
            sample_run_metrics_dtos=dtos.sample_sequencing_metrics, sequencing_run=sequencing_run
        )
        self._update_sample(
            sample_run_metrics_dtos=dtos.sample_sequencing_metrics,
            sequencing_date=sequencing_run.completed_at,
        )
        if dry_run:
            self.store.rollback()
            LOG.info(
                f"Dry run, no entries will be added to database for SMRT cell {run_data.full_path}."
            )
            return
        LOG.debug(f"Data stored in statusDB for run {run_data.sequencing_run_name}")
        self.store.commit_to_store()
