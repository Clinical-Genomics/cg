"""Fixtures for the tests of the IlluminaPostProcessingService."""

from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.illumina_services.illumina_post_processing_service.illumina_post_processing_service import (
    IlluminaPostProcessingService,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def illumina_post_postprocessing_service(
    store: Store,
    real_housekeeper_api: HousekeeperAPI,
    selected_novaseq_x_sample_ids: list[str],
    helpers: StoreHelpers,
) -> IlluminaPostProcessingService:
    """Return an instance of the IlluminaPostProcessingService."""
    for sample_id in selected_novaseq_x_sample_ids:
        helpers.add_sample(store, internal_id=sample_id)
    return IlluminaPostProcessingService(
        status_db=store, housekeeper_api=real_housekeeper_api, dry_run=False
    )
