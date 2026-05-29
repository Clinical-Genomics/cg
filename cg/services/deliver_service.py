import logging
from http.client import HTTPException

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.exc import MultipleAnalysesToDeliverError, TrailblazerAPIHTTPError
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case, Order
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class DeliverService:
    def __init__(self, status_db: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.status_db = status_db
        self.trailblazer_api = trailblazer_api
        self.mark_as_delivered_service = MarkAsDeliveredService(
            status_db=status_db, trailblazer_api=trailblazer_api
        )

    def deliver_all_cases(self) -> None:
        order_dict: dict[Order, list[Analysis]] = self._get_order_analyses_dictionary()
        if len(order_dict) == 0:
            LOG.warning("No analyses found to deliver.")
            return
        for order, analyses in order_dict.items():
            self._deliver_order(order=order, analyses=analyses)

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
                if self._is_order_closable(order):
                    order.is_open = False
            case _:
                raise MultipleAnalysesToDeliverError(f"Multiple analyses found for case {case_id}")

    def deliver_order(self, ticket_id: int, signature: str):
        # TODO update to reflect changes in deliver_all_cases
        order: Order = self.status_db.get_order_by_ticket_id_strict(ticket_id)

        undelivered_trailblazer_analyses = self.trailblazer_api.get_analyses_to_deliver(order.id)
        uploaded_analyses_to_deliver = self.status_db.get_uploaded_analyses(
            [analysis.id for analysis in undelivered_trailblazer_analyses]
        )
        if uploaded_analyses_to_deliver:
            self.mark_as_delivered_service.mark_analyses(
                analyses=uploaded_analyses_to_deliver, signature=signature
            )
            if self._is_order_closable(order):
                order.is_open = False
        else:
            LOG.warning("No analysis in the order ready to deliver")

    def _deliver_order(self, order: Order, analyses: list[Analysis]) -> None:
        # TODO consider whether to keep double commit-rollbacks and separation from methods
        if self._deliver_analyses_in_order(order=order, analyses=analyses):
            self.status_db.commit_to_store()
        else:
            self.status_db.rollback()
            return

        if self._close_order_and_ticket_if_applicable(order=order):
            self.status_db.commit_to_store()
        else:
            self.status_db.rollback()

    def _deliver_analyses_in_order(self, order: Order, analyses: list[Analysis]) -> bool:
        # TODO docstring
        success: bool = True
        LOG.info(f"Delivering {len(analyses)} analyses of ticket {order.ticket_id}.")
        try:
            self.mark_as_delivered_service.mark_analyses(analyses=analyses)
            self._freshdesk_send_delivery_message(order=order, analyses=analyses)
        except TrailblazerAPIHTTPError:
            LOG.error(
                f"Failed to deliver analyses in Trailblazer for order {order.id}. "
                f"Aborting delivery message for ticket {order.ticket_id}."
            )
            success = False
        except HTTPException:
            self.mark_as_delivered_service.unmark_analyses(analyses)
            LOG.error(
                f"Failed to send delivery message for ticket {order.ticket_id}. "
                f"Rolling back delivery status in Trailblazer and StatusDB for order {order.id}."
            )
            success = False
        return success

    def _close_order_and_ticket_if_applicable(self, order: Order) -> bool:
        # TODO docstring
        success = True
        try:
            if self._is_order_closable(order):
                LOG.info(f"Closing order {order.id} in StatusDB.")
                order.is_open = False
                self._freshdesk_close_ticket_if_open(order=order)
        except TrailblazerAPIHTTPError:
            LOG.error(
                f"Failed to check whether order {order.id} could be closed. Will not close ticket {order.ticket_id} in Freshdesk."
            )
            success = False
        except HTTPException:
            LOG.error(
                f"Failed to close ticket {order.ticket_id} in Freshdesk. "
                f"Rolling back closing order {order.id} in StatusDB."
            )
            # TODO failing to close freshdesk ticket does not necessarily mean order should be re-opened
            success = False
        return success

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

    def _freshdesk_send_delivery_message(self, order: Order, analyses: list[Analysis]):
        # Implement in next iteration
        pass

    def _freshdesk_close_ticket_if_open(self, order: Order):
        # Implement in next iteration
        LOG.info(f"Checking whether whether ticket {order.ticket_id} can be closed.")
        pass
