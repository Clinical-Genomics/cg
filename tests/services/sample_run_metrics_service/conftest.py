import pytest

from cg.services.sample_run_metrics_service.sample_run_metrics_service import (
    SampleRunMetricsService,
)
from cg.store.store import Store


@pytest.fixture
def sample_run_metrics_service(
    store_with_illumina_sequencing_data: Store,
) -> SampleRunMetricsService:
    return SampleRunMetricsService(store_with_illumina_sequencing_data)
