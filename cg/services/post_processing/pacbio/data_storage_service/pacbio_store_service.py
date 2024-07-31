import logging

from cg.services.post_processing.abstract_classes import PostProcessingStoreService
from cg.services.post_processing.error_handler import handle_post_processing_errors
from cg.services.post_processing.exc import (
    PostProcessingDataTransferError,
    PostProcessingStoreDataError,
)
from cg.services.post_processing.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.post_processing.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
)
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.store.models import PacBioSequencingRun, PacBioSMRTCell
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class PacBioStoreService(PostProcessingStoreService):
    def __init__(self, store: Store, data_transfer_service: PacBioDataTransferService):
        self.store = store
        self.data_transfer_service = data_transfer_service

    def _create_run_device(self, run_device_dto: PacBioSMRTCellDTO) -> PacBioSMRTCell:
        return self.store.create_pac_bio_smrt_cell(run_device_dto)

    def _create_instrument_run(
        self, instrument_run_dto: PacBioSequencingRunDTO, smrt_cell: PacBioSMRTCell
    ) -> PacBioSequencingRun:
        return self.store.create_pac_bio_sequencing_run(
            sequencing_run_dto=instrument_run_dto, smrt_cell=smrt_cell
        )

    def _create_sample_run_metrics(
        self,
        sample_run_metrics_dtos: list[PacBioSampleSequencingMetricsDTO],
        sequencing_run: PacBioSequencingRun,
    ):
        for sample_run_metric in sample_run_metrics_dtos:
            self.store.create_pac_bio_sample_sequencing_run(
                sample_run_metrics_dto=sample_run_metric, sequencing_run=sequencing_run
            )

    @handle_post_processing_errors(
        to_except=(PostProcessingDataTransferError, ValueError),
        to_raise=PostProcessingStoreDataError,
    )
    def store_post_processing_data(self, run_data: PacBioRunData, dry_run: bool = False):
        dtos: PacBioDTOs = self.data_transfer_service.get_post_processing_dtos(run_data)
        smrt_cell: PacBioSMRTCell = self._create_run_device(dtos.run_device)
        sequencing_run: PacBioSequencingRun = self._create_instrument_run(
            instrument_run_dto=dtos.sequencing_run, smrt_cell=smrt_cell
        )
        self._create_sample_run_metrics(
            sample_run_metrics_dtos=dtos.sample_sequencing_metrics, sequencing_run=sequencing_run
        )
        if dry_run:
            self.store.rollback()
            LOG.info(
                f"Dry run, no entries will be added to database for SMRT cell {run_data.full_path}."
            )
        else:
            self.store.commit_to_store()
