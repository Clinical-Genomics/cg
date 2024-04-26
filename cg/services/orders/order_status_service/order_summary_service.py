from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.dto.case_summary import CaseSummary
from cg.services.orders.order_status_service.dto.order_summary import OrderSummary
from cg.services.orders.order_status_service.utils import create_summaries
from cg.store.models import Order
from cg.store.store import Store


class OrderSummaryService:
    def __init__(self, analysis_client: TrailblazerAPI, store: Store) -> None:
        self.analysis_client = analysis_client
        self.store = store

    def get_summary(self, order_id: int) -> OrderSummary:
        return self.get_summaries([order_id])[0]

    def get_summaries(self, order_ids: list[int]) -> list[OrderSummary]:
        orders: list[Order] = self.store.get_orders_by_ids(order_ids)
        cases: list[CaseSummary] = self._get_case_summaries(order_ids)
        analyses: list[AnalysisSummary] = self.analysis_client.get_summaries(order_ids)
        return create_summaries(orders=orders, analysis_summaries=analyses, case_summaries=cases)

    def _get_case_summaries(self, order_ids: list[int]):
        summaries: list[CaseSummary] = []

        for order_id in order_ids:
            not_received: int = self.store.get_case_not_received_count(order_id)
            in_preparation: int = self.store.get_case_in_preparation_count(order_id)
            in_sequencing: int = self.store.get_case_in_sequencing_count(order_id)

            summary = CaseSummary(
                order_id=order_id,
                not_received=not_received,
                in_preparation=in_preparation,
                in_sequencing=in_sequencing,
            )
            summaries.append(summary)

        return summaries
