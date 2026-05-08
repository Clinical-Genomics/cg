from cg.apps.tb.api import TrailblazerAPI
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Case
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
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)

    def _get_undelivered_analyses_from_trailblazer(self):
        return

    def _get_uploaded_analyses(self):
        return
