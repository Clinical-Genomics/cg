"""Fixtures for the tests of the IlluminaPostProcessingService."""

from datetime import datetime
from pathlib import Path

import pytest
from housekeeper.store.models import Bundle

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.devices import DeviceType
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaSampleSequencingMetricsDTO,
)
from cg.services.illumina_services.illumina_post_processing_service.illumina_post_processing_service import (
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
) -> IlluminaPostProcessingService:
    """Return an instance of the IlluminaPostProcessingService."""
    for sample_id in selected_novaseq_x_sample_ids:
        helpers.add_sample(store, internal_id=sample_id)
    return IlluminaPostProcessingService(
        status_db=store, housekeeper_api=real_housekeeper_api, dry_run=False
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


@pytest.fixture
def mapped_metric():
    return IlluminaSampleSequencingMetricsDTO(
        sample_id="sample",
        type=DeviceType.ILLUMINA,
        flow_cell_lane=1,
        total_reads_in_lane=100,
        base_passing_q30_percent=0.9,
        base_mean_quality_score=30,
        yield_=100,
        yield_q30=0.9,
        created_at=datetime.now(),
    )


@pytest.fixture
def undetermined_metric():
    return IlluminaSampleSequencingMetricsDTO(
        sample_id="sample",
        flow_cell_lane=1,
        type=DeviceType.ILLUMINA,
        total_reads_in_lane=100,
        base_passing_q30_percent=0.8,
        base_mean_quality_score=20,
        yield_=100,
        yield_q30=0.8,
        created_at=datetime.now(),
    )
