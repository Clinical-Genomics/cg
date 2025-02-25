"""Module for the Pacbio data transfer object creation service."""

import logging

from pydantic import ValidationError

from cg.services.run_devices.abstract_classes import PostProcessingDataTransferService
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import (
    PostProcessingDataTransferError,
    PostProcessingRunFileManagerError,
)
from cg.services.run_devices.pacbio.data_transfer_service.dto import (
    PacBioDTOs,
    PacBioSampleSequencingMetricsDTO,
    PacBioSequencingRunDTO,
    PacBioSMRTCellDTO,
)
from cg.services.run_devices.pacbio.data_transfer_service.utils import (
    get_sample_sequencing_metrics_dtos,
    get_sequencing_run_dto,
    get_smrt_cell_dto,
)
from cg.services.run_devices.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.run_devices.pacbio.metrics_parser.models import PacBioMetrics
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData

LOG = logging.getLogger(__name__)


class PacBioDataTransferService(PostProcessingDataTransferService):
    def __init__(self, metrics_service: PacBioMetricsParser):
        self.metrics_service: PacBioMetricsParser = metrics_service

    @handle_post_processing_errors(
        to_except=(PostProcessingRunFileManagerError, ValidationError),
        to_raise=PostProcessingDataTransferError,
    )
    def get_post_processing_dtos(self, run_data: PacBioRunData) -> PacBioDTOs:
        metrics: PacBioMetrics = self.metrics_service.parse_metrics(run_data)
        smrt_cell_dto: PacBioSMRTCellDTO = get_smrt_cell_dto(metrics)
        sequencing_run_dto: PacBioSequencingRunDTO = get_sequencing_run_dto(
            metrics=metrics, run_data=run_data
        )
        sample_sequencing_metrics_dtos: list[PacBioSampleSequencingMetricsDTO] = (
            get_sample_sequencing_metrics_dtos(metrics.samples)
        )
        LOG.debug("DTOs created")
        return PacBioDTOs(
            run_device=smrt_cell_dto,
            sequencing_run=sequencing_run_dto,
            sample_sequencing_metrics=sample_sequencing_metrics_dtos,
        )
