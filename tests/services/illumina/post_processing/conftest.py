"""Fixtures for the tests of the IlluminaPostProcessingService."""

from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.devices import DeviceType
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.post_processing.post_processing_service import (
    IlluminaPostProcessingService,
)
from cg.store.models import IlluminaFlowCell
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def illumina_post_postprocessing_service(
    store: Store,
    real_housekeeper_api: HousekeeperAPI,
    selected_novaseq_x_sample_ids: list[str],
    helpers: StoreHelpers,
    illumina_demultiplexed_runs_post_processing_hk_api: HousekeeperAPI,
    tmp_illumina_demultiplexed_runs_directory: str,
) -> IlluminaPostProcessingService:
    """Return an instance of the IlluminaPostProcessingService."""
    for sample_id in selected_novaseq_x_sample_ids:
        helpers.add_sample(store, internal_id=sample_id)
    return IlluminaPostProcessingService(
        status_db=store,
        housekeeper_api=illumina_demultiplexed_runs_post_processing_hk_api,
        dry_run=False,
        demultiplexed_runs_dir=Path(tmp_illumina_demultiplexed_runs_directory),
    )


@pytest.fixture
def illumina_flow_cell(
    novaseq_x_demux_runs_flow_cell: IlluminaRunDirectoryData,
) -> IlluminaFlowCell:
    """Return an Illumina flow cell."""
    return IlluminaFlowCell(
        internal_id=novaseq_x_demux_runs_flow_cell.id,
        type=DeviceType.ILLUMINA,
        model=novaseq_x_demux_runs_flow_cell.run_parameters.get_flow_cell_model(),
    )
