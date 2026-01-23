from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunDTO,
    PacbioSequencingRunResponse,
    PacbioSequencingRunUpdateRequest,
    PacbioSmrtCellMetricsDTO,
    PacbioSmrtCellMetricsResponse,
)
from cg.store.models import PacbioSMRTCellMetrics
from cg.store.store import Store


class PacbioSequencingRunsService:
    def __init__(self, store: Store):
        self.store = store

    def get_sequencing_runs_by_name(self, run_name: str) -> PacbioSmrtCellMetricsResponse:
        metrics: list[PacbioSmrtCellMetricsDTO] = []
        db_smrt_cell_metrics: list[PacbioSMRTCellMetrics] = (
            self.store.get_pacbio_smrt_cell_metrics_by_run_internal_id(run_name)
        )
        for metric in db_smrt_cell_metrics:
            metric_dict = metric.to_dict()
            metric_dict["internal_id"] = metric.device.internal_id
            metric_dict["run_name"] = metric.sequencing_run.internal_id
            metrics.append(PacbioSmrtCellMetricsDTO.model_validate(metric_dict))
        return PacbioSmrtCellMetricsResponse(runs=metrics)

    def get_sequencing_runs(self, page: int = 0, page_size: int = 0) -> PacbioSequencingRunResponse:
        db_runs, total_count = self.store.get_pacbio_sequencing_runs(page=page, page_size=page_size)
        runs: list[PacbioSequencingRunDTO] = []
        for db_run in db_runs:
            run = PacbioSequencingRunDTO(
                id=db_run.id,
                run_name=db_run.internal_id,
                comment=db_run.comment,
                processed=db_run.processed,
            )
            runs.append(run)
        return PacbioSequencingRunResponse(pacbio_sequencing_runs=runs, total_count=total_count)

    def update_sequencing_run(self, update_request: PacbioSequencingRunUpdateRequest) -> None:
        if update_request.comment is not None:
            self.store.update_pacbio_sequencing_run_comment(
                id=update_request.id, comment=update_request.comment
            )

        if update_request.processed is not None:
            self.store.update_pacbio_sequencing_run_processed(
                id=update_request.id, processed=update_request.processed
            )
