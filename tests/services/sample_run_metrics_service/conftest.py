from unittest import mock

import pytest

from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioDTOs
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.sample_run_metrics_service.sample_run_metrics_service import (
    SampleRunMetricsService,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def sample_run_metrics_service(
    store_with_illumina_sequencing_data: Store,
    pacbio_barcoded_run_data: PacBioRunData,
    pac_bio_store_service: PacBioStoreService,
    pac_bio_dtos: PacBioDTOs,
    pacbio_barcoded_sample_internal_id: str,
    helpers: StoreHelpers,
) -> SampleRunMetricsService:
    helpers.add_sample(
        store=store_with_illumina_sequencing_data, internal_id=pacbio_barcoded_sample_internal_id
    )
    pac_bio_store_service.store = store_with_illumina_sequencing_data
    with mock.patch(
        "cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service.PacBioDataTransferService.get_post_processing_dtos",
        return_value=pac_bio_dtos,
    ):
        pac_bio_store_service.store_post_processing_data(pacbio_barcoded_run_data)
    return SampleRunMetricsService(store_with_illumina_sequencing_data)
