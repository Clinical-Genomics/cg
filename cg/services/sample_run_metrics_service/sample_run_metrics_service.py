from cg.server.endpoints.sequencing_metrics.dtos import PacbioSequencingMetricsRequest
from cg.services.sample_run_metrics_service.dtos import (
    IlluminaSequencingMetrics,
    PacbioSequencingMetrics,
)
from cg.services.sample_run_metrics_service.utils import create_metrics_dto
from cg.store.models import IlluminaSequencingRun, PacbioSampleSequencingMetrics
from cg.store.store import Store


class SampleRunMetricsService:
    def __init__(self, store: Store):
        self.store = store

    def get_illumina_metrics(self, flow_cell_name: str) -> list[IlluminaSequencingMetrics]:
        run: IlluminaSequencingRun = self.store.get_illumina_sequencing_run_by_device_internal_id(
            flow_cell_name
        )
        return create_metrics_dto(run.sample_metrics) if run else []

    def get_pacbio_metrics(
        self, metrics_request: PacbioSequencingMetricsRequest
    ) -> list[PacbioSequencingMetrics]:
        response: list[PacbioSequencingMetrics] = []
        sequencing_metrics: list[PacbioSampleSequencingMetrics] = (
            self.store.get_pacbio_sample_sequencing_metrics(
                sample_id=metrics_request.sample_id, smrt_cell_id=metrics_request.smrt_cell_id
            )
        )
        for db_metric in sequencing_metrics:
            metric = PacbioSequencingMetrics(
                hifi_mean_read_length=db_metric.hifi_mean_read_length,
                hifi_median_read_quality=db_metric.hifi_median_read_quality,
                hifi_reads=db_metric.hifi_reads,
                hifi_yield=db_metric.hifi_yield,
                sample_id=db_metric.sample.internal_id,
                smrt_cell_id=db_metric.instrument_run.device.internal_id,
            )
            response.append(metric)
        return response
