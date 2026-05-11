from cg.apps.tb.api import TrailblazerAPI
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
        # Look at analysis of case
        # ANy uploaded?
        uploaded_analyses: list[Analysis] = [
            analysis for analysis in case.analyses if analysis.uploaded_at
        ]
        # For each analysis that was uploaded is it delivered in TB
        analyses_with_status: list[tuple[Analysis, str]] = (
            self.trailblazer_api.get_delivery_statuses(uploaded_analyses)
        )
        analyses_to_deliver: list[Analysis] = [
            analysis for analysis, status in analyses_with_status if status != "delivered"
        ]
        # If more than one still in the list, raise an Error
        if len(analyses_to_deliver) > 1:
            raise Exception

        # Deliver the singel analysis
        self.mark_as_delivered_service.mark_analyses(analyses=analyses_to_deliver)

    def _get_undelivered_analyses_from_trailblazer(self):
        return

    def _get_uploaded_analyses(self):
        return
