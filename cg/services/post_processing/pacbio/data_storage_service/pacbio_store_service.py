from cg.services.post_processing.abstract_classes import (
    PostProcessingStoreService,
    PostProcessingDataTransferService,
)
from cg.services.post_processing.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSMRTCellDTO,
    PacBioSequencingRunDTO,
    PacBioSampleSequencingMetricsDTO,
)
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.store.store import Store


class PacBioStoreService(PostProcessingStoreService):
    def __init__(self, store: Store, data_transfer_service: PostProcessingDataTransferService):
        super().__init__(store=store, data_transfer_service=data_transfer_service)

    def _create_run_device(self, run_device_dto: PacBioSMRTCellDTO):
        pass

    def _create_instrument_run(self, instrument_run_dto: PacBioSequencingRunDTO):
        pass

    def _create_sample_run_metrics(
        self, sample_run_metrics_dtos: list[PacBioSampleSequencingMetricsDTO]
    ):
        pass

    def store_post_processing_data(self, run_data: PacBioRunData):
        dtos: PacBioDTOs = self.data_transfer_service.get_post_processing_dtos()
