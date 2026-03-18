from datetime import datetime

from cg.apps.tb.api import TrailblazerAPI
from cg.constants import Workflow
from cg.store.models import Analysis, Case, CaseSample
from cg.store.store import Store


class MarkAsDeliveredService:
    def __init__(self, status_db: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.status_db = status_db
        self.trailblazer_api = trailblazer_api

    def mark_analysis(self, analysis: Analysis):
        case: Case = analysis.case
        for case_sample in case.links:
            if self._should_sample_be_delivered(case_sample):
                case_sample.sample.delivered_at = datetime.now()
        self.trailblazer_api.mark_analyses_as_delivered(trailblazer_ids=[analysis.trailblazer_id])

    def _should_sample_be_delivered(self, case_sample: CaseSample) -> bool:
        return (
            case_sample.is_original
            and not case_sample.sample.delivered_at
            and self._passes_on_reads(case_sample)
        )

    @staticmethod
    def _passes_on_reads(case_sample: CaseSample) -> bool:
        if case_sample.case.data_analysis in [Workflow.MICROSALT, Workflow.TAXPROFILER]:
            return case_sample.sample.reads >= case_sample.sample.expected_reads_for_sample
        else:
            return True
