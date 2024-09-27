from unittest.mock import Mock

import pytest

from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioDTOs
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def pac_bio_store_service(store: Store, helpers: StoreHelpers, pac_bio_dtos: PacBioDTOs):
    helpers.add_sample(
        store=store, internal_id=pac_bio_dtos.sample_sequencing_metrics[0].sample_internal_id
    )
    return PacBioStoreService(
        store=store, data_transfer_service=PacBioDataTransferService(metrics_service=Mock())
    )
