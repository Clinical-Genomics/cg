from datetime import datetime

from cg.store.models import Analysis, Case, CaseSample
from cg.store.store import Store


class MarkSamplesAsDeliveredService:
    def __init__(self, status_db: Store) -> None:
        self.status_db = status_db

    def mark_samples_as_delivered(self, trailblazer_id: int):
        # TODO deal with the exception when there is no analysis
        analysis: Analysis = self.status_db.get_analysis_by_trailblazer_id(trailblazer_id)
        case: Case = analysis.case
        for case_sample in case.links:
            # TODO group meditation on attribute name
            if (
                case_sample.is_original
                and not case_sample.sample.delivered_at
                and passes_on_reads(case_sample)
            ):
                case_sample.sample.delivered_at = datetime.now()

    def _should_sample_be_delivered(self, case_sample: CaseSample) -> bool:
        pass
