import logging

from cg.apps.tb.api import TrailblazerAPI
from cg.exc import MultipleAnalysesToDeliverError
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


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
        uploaded_trailblazer_ids: list[int] = [
            analysis.trailblazer_id for analysis in uploaded_analyses if analysis.trailblazer_id
        ]
        analyses_with_status: list[tuple[int, bool]] = self.trailblazer_api.are_analyses_delivered(
            uploaded_trailblazer_ids
        )
        undelivered_trailblazer_ids = [
            trailblazer_id
            for trailblazer_id, is_delivered in analyses_with_status
            if not is_delivered
        ]
        analyses_to_deliver = []
        for analysis in uploaded_analyses:
            if analysis.trailblazer_id in undelivered_trailblazer_ids:
                analyses_to_deliver.append(analysis)
        match len(analyses_to_deliver):
            case 0:
                LOG.warning(f"No analysis found to deliver for case {case_id}.")
            case 1:
                self.mark_as_delivered_service.mark_analyses(analyses=analyses_to_deliver)
            case _:
                raise MultipleAnalysesToDeliverError(f"Multiple analyses found for case {case_id}")

    def _get_undelivered_analyses_from_trailblazer(self):
        return

    def _get_uploaded_analyses(self):
        return
