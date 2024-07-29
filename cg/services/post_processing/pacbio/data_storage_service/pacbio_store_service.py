from cg.services.post_processing.abstract_classes import (
    PostProcessingStoreService,
)
from cg.services.post_processing.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.post_processing.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSMRTCellDTO,
    PacBioSequencingRunDTO,
    PacBioSampleSequencingMetricsDTO,
)
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.store.models import PacBioSMRTCell, PacBioSequencingRun
from cg.store.store import Store


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

    def store_post_processing_data(self, run_data: PacBioRunData):
        dtos: PacBioDTOs = self.data_transfer_service.get_post_processing_dtos()
        smrt_cell: PacBioSMRTCell = self._create_run_device(dtos.run_device)
        sequencing_run: PacBioSequencingRun = self._create_instrument_run(
            instrument_run_dto=dtos.sequencing_run, smrt_cell=smrt_cell
        )
        self._create_sample_run_metrics(
            sample_run_metrics_dtos=dtos.sample_sequencing_metrics, sequencing_run=sequencing_run
        )
        self.store.commit_to_store()
