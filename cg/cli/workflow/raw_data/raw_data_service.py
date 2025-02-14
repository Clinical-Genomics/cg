import datetime as dt

from cg.apps.tb.api import TrailblazerAPI
from cg.constants.constants import Workflow
from cg.constants.tb import AnalysisStatus, AnalysisType
from cg.exc import CaseNotFoundError
from cg.meta.workflow.utils.utils import MAP_TO_TRAILBLAZER_PRIORITY
from cg.store.models import Analysis, Case
from cg.store.store import Store


class RawDataAnalysisService:
    def __init__(self, store: Store, trailblazer_api: TrailblazerAPI):
        self.store = store
        self.trailblazer_api = trailblazer_api

    def store_analysis(self, case_id: str) -> None:
        case: Case = self._get_case(case_id)
        self._add_analysis_to_store(case)
        self._add_analysis_to_trailblazer(case)

    def _get_case(self, case_id: str) -> Case:
        if case := self.store.get_case_by_internal_id(case_id):
            return case
        raise CaseNotFoundError(f"Case {case_id} not found.")

    def _add_analysis_to_store(self, case: Case) -> None:
        new_analysis: Analysis = self.store.add_analysis(
            workflow=Workflow.RAW_DATA,
            completed_at=dt.datetime.now(),
            primary=True,
            started_at=dt.datetime.now(),
            case_id=case.id,
        )
        self.store.session.add(new_analysis)
        self.store.session.commit()

    def _add_analysis_to_trailblazer(self, case: Case) -> None:
        self.trailblazer_api.add_pending_analysis(
            case_id=case.internal_id,
            analysis_type=AnalysisType.OTHER,
            config_path="",
            order_id=case.latest_order.id,
            out_dir="",
            priority=MAP_TO_TRAILBLAZER_PRIORITY[case.priority],
            workflow=Workflow.RAW_DATA,
            ticket=case.latest_ticket,
        )
        self.trailblazer_api.set_analysis_status(
            case_id=case.internal_id, status=AnalysisStatus.COMPLETED
        )
