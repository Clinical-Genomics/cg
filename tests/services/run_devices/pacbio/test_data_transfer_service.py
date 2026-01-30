from unittest.mock import Mock, create_autospec

import pytest

from cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioDTOs
from cg.services.run_devices.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.run_devices.pacbio.metrics_parser.models import PacBioMetrics
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData


# TODO
@pytest.mark.skip("Sebas will fix it")
def test_get_post_processing_dtos(
    pacbio_barcoded_run_data: PacBioRunData,
    pac_bio_dtos: PacBioDTOs,
    pac_bio_metrics: PacBioMetrics,
):
    # GIVEN a DataTransferService
    metrics_service: PacBioMetricsParser = create_autospec(PacBioMetricsParser)
    metrics_service.parse_metrics = Mock(return_value=pac_bio_metrics)
    service = PacBioDataTransferService(metrics_service=metrics_service)

    # WHEN calling get_post_processing_dtos
    dtos: PacBioDTOs = service.get_post_processing_dtos(pacbio_barcoded_run_data)

    # THEN the result is as expected
    assert dtos == pac_bio_dtos
