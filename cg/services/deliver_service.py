import logging

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.clients.freshdesk.constants import Status
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.exc import (
    FreshdeskDeliveryMessageError,
    FreshdeskGetTicketError,
    FreshdeskUpdateTicketError,
    MultipleAnalysesToDeliverError,
    TrailblazerAnalysisDeliveryError,
    TrailblazerFailedToGetAnalysesError,
)
from cg.services.delivery_message.utils import get_message
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case, Order
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliverService:
    def __init__(
        self, freshdesk_client: FreshdeskClient, status_db: Store, trailblazer_api: TrailblazerAPI
    ) -> None:
        self.status_db = status_db
        self.trailblazer_api = trailblazer_api
        self.mark_as_delivered_service = MarkAsDeliveredService(
            status_db=status_db, trailblazer_api=trailblazer_api
        )
        self.freshdesk_client = freshdesk_client

    def deliver_all_available(self) -> bool:
        order_dict: dict[Order, list[Analysis]] = self._get_order_analyses_dictionary()
        if len(order_dict) == 0:
            LOG.warning("No analyses found to deliver.")
            return True
        are_all_orders_delivered: list[bool] = []
        for order, analyses in order_dict.items():
            order_successful: bool = self._deliver(order=order, analyses=analyses, signature=None)
            are_all_orders_delivered.append(order_successful)
        return all(are_all_orders_delivered)

    def deliver_case(self, case_id: str, signature: str):
        analyses_to_deliver: list[Analysis] = self._get_undelivered_analyses_for_case(case_id)
        match len(analyses_to_deliver):
            case 0:
                LOG.warning(f"No analysis found to deliver for case {case_id}.")
            case 1:
                order: Order = analyses_to_deliver[0].order
                self._deliver(order=order, analyses=analyses_to_deliver, signature=signature)
            case _:
                raise MultipleAnalysesToDeliverError(f"Multiple analyses found for case {case_id}")

    def deliver_order(self, ticket_id: int, signature: str):
        order: Order = self.status_db.get_order_by_ticket_id_strict(ticket_id)
        undelivered_trailblazer_analyses = self.trailblazer_api.get_analyses_to_deliver_for_order(
            order.id
        )
        uploaded_analyses_to_deliver = self.status_db.get_uploaded_analyses(
            [analysis.id for analysis in undelivered_trailblazer_analyses]
        )
        if uploaded_analyses_to_deliver:
            self._deliver(order=order, analyses=uploaded_analyses_to_deliver, signature=signature)
        else:
            LOG.warning("No analysis in the order ready to deliver")

    def _deliver(
        self, order: Order, analyses: list[Analysis], signature: str | None = None
    ) -> bool:
        try:
            self._deliver_order(order=order, analyses=analyses, signature=signature)
        except TrailblazerAnalysisDeliveryError as error:
            self.status_db.rollback()
            LOG.error(f"Failed to mark analyses as delivered in Trailblazer for order {order.id}")
            LOG.exception(error)
            return False
        except (TrailblazerFailedToGetAnalysesError, FreshdeskDeliveryMessageError) as error:
            self.status_db.rollback()
            self.mark_as_delivered_service.unmark_analyses(analyses)
            LOG.error(f"Failed to send delivery message for ticket {order.ticket_id}")
            LOG.exception(error)
            return False
        except (FreshdeskGetTicketError, FreshdeskUpdateTicketError) as error:
            order.is_open = True
            self.status_db.commit_to_store()
            LOG.error(f"Failed to close ticket {order.ticket_id} in Freshdesk")
            LOG.exception(error)
            return False
        else:
            self.status_db.commit_to_store()
            return True

    def _deliver_order(
        self, order: Order, analyses: list[Analysis], signature: str | None = None
    ) -> None:
        LOG.info(f"Delivering {len(analyses)} analyses of ticket {order.ticket_id}.")
        self.mark_as_delivered_service.mark_analyses(analyses=analyses, signature=signature)
        self.mark_as_delivered_service.close_order_in_status_db_if_closable(order)
        self._freshdesk_send_delivery_message(order=order, analyses=analyses)
        self._freshdesk_close_ticket_if_open(order=order)

    def _get_undelivered_analyses_for_case(self, case_id: str) -> list[Analysis]:
        undelivered_trailblazer_analyses: list[TrailblazerAnalysis] = (
            self.trailblazer_api.get_analyses_to_deliver_for_case(case_id)
        )
        undelivered_trailblazer_ids = [analysis.id for analysis in undelivered_trailblazer_analyses]
        analyses_to_deliver: list[Analysis] = self.status_db.get_uploaded_analyses(
            undelivered_trailblazer_ids
        )
        return analyses_to_deliver

    def _get_order_analyses_dictionary(self) -> dict[Order, list[Analysis]]:
        """
        Returns a dictionary with orders as keys and lists of analyses as values. Only includes
        analyses that are marked as uploaded in StatusDB and not yet marked as delivered in
        Trailblazer.
        """
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

    def _freshdesk_send_delivery_message(self, order: Order, analyses: list[Analysis]):
        cases: list[Case] = [analysis.case for analysis in analyses]
        message: str = get_message(cases=cases, store=self.status_db)
        self.freshdesk_client.reply_to_ticket(ticket_id=order.ticket_id, message=message)

    def _freshdesk_close_ticket_if_open(self, order: Order):
        if not order.is_open:
            if self.freshdesk_client.get_ticket(order.ticket_id).status == Status.OPEN:
                self.freshdesk_client.update_ticket(ticket_id=order.ticket_id, status=Status.CLOSED)
        else:
            return
