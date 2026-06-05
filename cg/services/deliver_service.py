import logging

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.exc import (
    FreshdeskClosingTicketError,
    FreshdeskDeliveryMessageError,
    MultipleAnalysesToDeliverError,
    TrailblazerAnalysisDeliveryError,
    TrailblazerFailedToGetAnalysesError,
)
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Order
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliverService:
    def __init__(self, status_db: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.status_db = status_db
        self.trailblazer_api = trailblazer_api
        self.mark_as_delivered_service = MarkAsDeliveredService(
            status_db=status_db, trailblazer_api=trailblazer_api
        )

    def deliver_all_available(self) -> None:
        # TODO: Make the service fail if any exception is caught
        # TODO: Discuss if this should be in the CLI layer
        order_dict: dict[Order, list[Analysis]] = self._get_order_analyses_dictionary()
        if len(order_dict) == 0:
            LOG.warning("No analyses found to deliver.")
            return
        for order, analyses in order_dict.items():
            try:
                self._deliver_order(order=order, analyses=analyses)
            except TrailblazerAnalysisDeliveryError:
                # Samples marked but nothing in TB nor FD
                self.status_db.rollback()
            except (TrailblazerFailedToGetAnalysesError, FreshdeskDeliveryMessageError):
                # Samples marked TB analysis marked, no FD
                self.status_db.rollback()
                self.mark_as_delivered_service.unmark_analyses(analyses)
            except FreshdeskClosingTicketError:
                # Samples marked TB analysis marked, delivery message sent in FD, potentially order closed in StatusDB
                order.is_open = True
                self.status_db.commit_to_store()
            else:
                self.status_db.commit_to_store()

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
                self.mark_as_delivered_service.close_order_in_status_db_if_closable(order)
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
            self._deliver_order(
                order=order, analyses=uploaded_analyses_to_deliver, signature=signature
            )
        else:
            LOG.warning("No analysis in the order ready to deliver")

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
        # Implement in next iteration
        pass

    def _freshdesk_close_ticket_if_open(self, order: Order):
        # Implement in next iteration
        if not order.is_open:
            # call freshesk
            pass
        else:
            return
