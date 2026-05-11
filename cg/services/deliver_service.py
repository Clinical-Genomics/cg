from cg.apps.tb.api import TrailblazerAPI
from cg.exc import MultipleAnalysesToDeliverError
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case
from cg.store.store import Store


class DeliverService:
    def __init__(self, status_db: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.status_db = status_db
        self.trailblazer_api = trailblazer_api
        self.mark_as_delivered_service = MarkAsDeliveredService(
            status_db=status_db, trailblazer_api=trailblazer_api
        )

    def deliver_all_cases(self):
        # get all undelivered analyses from trailblazer
        # get uploaded analyses
        # mark analyses as delivered
        pass

    def deliver_case(self, case_id: str):
        # TODO add user
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        uploaded_analyses: list[Analysis] = [
            analysis for analysis in case.analyses if analysis.uploaded_at
        ]
        analyses_with_status: list[tuple[Analysis, bool]] = (
            self.trailblazer_api.are_analyses_delivered(uploaded_analyses)
        )
        analyses_to_deliver: list[Analysis] = [
            analysis for analysis, is_delivered in analyses_with_status if not is_delivered
        ]
        if len(analyses_to_deliver) > 1:
            raise MultipleAnalysesToDeliverError(f"Multiple analyses found for case {case_id}")
        if analyses_to_deliver:
            self.mark_as_delivered_service.mark_analyses(analyses=analyses_to_deliver)

    def _get_undelivered_analyses_from_trailblazer(self):
        return

    def _get_uploaded_analyses(self):
        return
