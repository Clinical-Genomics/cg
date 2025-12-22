from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunDTO,
    PacbioSequencingRunsResponse,
)
from cg.store.models import PacbioSequencingRun, PacbioSMRTCellMetrics
from cg.store.store import Store


class PacbioSequencingRunsService:
    def __init__(self, store: Store):
        self.store = store

    def get_sequencing_runs_by_name(self, run_name: str) -> PacbioSequencingRunsResponse:
        runs: list[PacbioSequencingRunDTO] = []
        db_runs: list[PacbioSMRTCellMetrics] = self.store.get_pacbio_smrt_cell_metrics_by_run_name(
            run_name
        )
        for db_run in db_runs:
            run_dict = db_run.to_dict()
            run_dict["internal_id"] = db_run.device.internal_id
            run = PacbioSequencingRunDTO.model_validate(run_dict)
            runs.append(run)
        return PacbioSequencingRunsResponse(runs=runs)

    def get_all_sequencing_runs(self) -> list[PacbioSequencingRun]:
        pass
