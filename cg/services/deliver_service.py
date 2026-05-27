import logging

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.clients.freshdesk.models import ReplyCreate
from cg.exc import MultipleAnalysesToDeliverError
from cg.services.delivery_message.utils import get_message
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case, Order
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliverService:
    def __init__(
        self, status_db: Store, trailblazer_api: TrailblazerAPI, freshdesk_client: FreshdeskClient
    ) -> None:
        self.status_db = status_db
        self.trailblazer_api = trailblazer_api
        self.mark_as_delivered_service = MarkAsDeliveredService(
            status_db=status_db, trailblazer_api=trailblazer_api
        )
        self.freshdesk_client = freshdesk_client

    def deliver_all_cases(self):

        # Get orders to deliver
        # For each order -> get all analyses -> build order-analyses dict
        # Iterate over order-analyses
        order_dict: dict[Order, list[Analysis]] = self._get_order_analyses_dictionary()
        for order, analyses in order_dict.items():
            self.mark_as_delivered_service.mark_analyses(analyses=analyses)
            try:
                delivery_message = get_message(cases=order.cases, store=self.status_db)
                delivery_message_html = delivery_message.replace(
                    "\n", "<br>"
                )  # Freshdesk takes HTML formatting
                # TODO possible intervention to prevent hot messages during demo/testing here
                reply = ReplyCreate(ticket_number=str(order.ticket_id), body=delivery_message_html)
                self.freshdesk_client.reply_to_ticket(reply=reply)
            except:
                self.mark_as_delivered_service.unmark_analyses(analyses)
            finally:
                if self._is_order_closable(order):
                    order.is_open = False
                    if self.freshdesk_client.is_order_open(order):
                        # Discuss if the freshdesk is_order_open should be inside close_ticket
                        self.freshdesk_client.close_ticket(order=order)
                    # TODO method to rollback
                # TODO commit

    def _is_order_closable(self, order: Order) -> bool:
        """
        Return True only if
        - we have a delivered TB analysis for each case and
        - each sample in the order has a "delivered_at" set

        Note, the second condition is only needed for partial deliveries in microSALT and taxprofiler.
        """
        delivered_analyses: list[TrailblazerAnalysis] = (
            self.trailblazer_api.get_delivered_analyses_for_order(order_id=order.id)
        )
        delivered_case_ids: set[str] = {analysis.case_id for analysis in delivered_analyses}
        case_ids_on_order: set[str] = {case.internal_id for case in order.cases}
        are_all_samples_delivered = all(
            sample.delivered_at for case in order.cases for sample in case.samples
        )
        return delivered_case_ids == case_ids_on_order and are_all_samples_delivered

    def _get_order_analyses_dictionary(self) -> dict[Order, list[Analysis]]:
        # TODO: add docstring
        undelivered_trailblazer_analyses: list[TrailblazerAnalysis] = (
            self.trailblazer_api.get_all_analyses_to_deliver()
        )
        uploaded_analyses_to_deliver: list[Analysis] = self.status_db.get_uploaded_analyses(
            trailblazer_ids=[analysis.id for analysis in undelivered_trailblazer_analyses]
        )
        order_analyses = {}
        for analysis in uploaded_analyses_to_deliver:
            if analysis.order in order_analyses:
                order_analyses[analysis.order].append(analysis)
            else:
                order_analyses[analysis.order] = [analysis]
        return order_analyses

    def deliver_case(self, case_id: str, signature: str):
        analyses_to_deliver: list[Analysis] = self._get_undelivered_analyses_for_case(case_id)
        match len(analyses_to_deliver):
            case 0:
                LOG.warning(f"No analysis found to deliver for case {case_id}.")
            case 1:
                self.mark_as_delivered_service.mark_analyses(
                    analyses=analyses_to_deliver, signature=signature
                )
                order: Order = analyses_to_deliver[0].order
                self.mark_as_delivered_service.close_order(order)
            case _:
                raise MultipleAnalysesToDeliverError(f"Multiple analyses found for case {case_id}")

    def deliver_order(self, ticket_id: int, signature: str):
        order: Order = self.status_db.get_order_by_ticket_id_strict(ticket_id)

        undelivered_trailblazer_analyses = self.trailblazer_api.get_analyses_to_deliver(order.id)
        uploaded_analyses_to_deliver = self.status_db.get_uploaded_analyses(
            [analysis.id for analysis in undelivered_trailblazer_analyses]
        )
        if uploaded_analyses_to_deliver:
            self.mark_as_delivered_service.mark_analyses(
                analyses=uploaded_analyses_to_deliver, signature=signature
            )
            self.mark_as_delivered_service.close_order(order)
        else:
            LOG.warning("No analysis in the order ready to deliver")

    def _get_undelivered_analyses_for_case(self, case_id: str) -> list[Analysis]:
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        uploaded_analyses: list[Analysis] = [
            analysis for analysis in case.analyses if analysis.uploaded_at
        ]
        undelivered_trailblazer_analyses: list[TrailblazerAnalysis] = (
            self.trailblazer_api.get_analyses_to_deliver_for_case(case_id)
        )
        undelivered_trailblazer_ids = [analysis.id for analysis in undelivered_trailblazer_analyses]
        analyses_to_deliver: list[Analysis] = []
        for analysis in uploaded_analyses:
            if analysis.trailblazer_id in undelivered_trailblazer_ids:
                analyses_to_deliver.append(analysis)

        return analyses_to_deliver
