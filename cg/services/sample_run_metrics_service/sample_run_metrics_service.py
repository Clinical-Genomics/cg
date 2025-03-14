from cg.server.endpoints.sequencing_metrics.dtos import PacbioSequencingMetricsRequest
from cg.services.sample_run_metrics_service.dtos import (
    IlluminaSequencingMetricsDTO,
    PacbioSequencingMetricsDTO,
)
from cg.services.sample_run_metrics_service.utils import create_metrics_dto
from cg.store.models import IlluminaSequencingRun, PacbioSampleSequencingMetrics
from cg.store.store import Store


class SampleRunMetricsService:
    def __init__(self, store: Store):
        self.store = store

    def get_illumina_metrics(self, flow_cell_name: str) -> list[IlluminaSequencingMetricsDTO]:
        run: IlluminaSequencingRun = self.store.get_illumina_sequencing_run_by_device_internal_id(
            flow_cell_name
        )
        return create_metrics_dto(run.sample_metrics) if run else []

    def get_pacbio_metrics(
        self, metrics_request: PacbioSequencingMetricsRequest
    ) -> list[PacbioSequencingMetricsDTO]:
        response: list[PacbioSequencingMetricsDTO] = []
        sequencing_metrics: list[PacbioSampleSequencingMetrics] = (
            self.store.get_pacbio_sample_sequencing_metrics(
                sample_id=metrics_request.sample_id, smrt_cell_ids=metrics_request.smrt_cell_ids
            )
        )
        for db_metrics in sequencing_metrics:
            metrics = PacbioSequencingMetricsDTO(
                hifi_mean_read_length=db_metrics.hifi_mean_read_length,
                hifi_median_read_quality=db_metrics.hifi_median_read_quality,
                hifi_reads=db_metrics.hifi_reads,
                hifi_yield=db_metrics.hifi_yield,
                sample_id=db_metrics.sample.internal_id,
                smrt_cell_id=db_metrics.instrument_run.device.internal_id,
            )
            response.append(metrics)
        return response
