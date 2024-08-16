from cg.services.sample_run_metrics_service.dtos import SequencingMetrics
from cg.services.sample_run_metrics_service.utils import create_metrics_dto
from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store


class SampleRunMetricsService:
    def __init__(self, store: Store):
        self.store = store

    def get_metrics(self, flow_cell_name: str) -> list[SequencingMetrics]:
        run: IlluminaSequencingRun = self.store.get_illumina_sequencing_run_by_device_internal_id(
            flow_cell_name
        )
        return create_metrics_dto(run.sample_metrics) if run else []
