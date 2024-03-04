from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.dto.order_status_summary import OrderSummary
from cg.services.orders.order_status_service.utils import create_summaries
from cg.store.models import Order
from cg.store.store import Store


class OrderStatusService:
    def __init__(self, analysis_client: TrailblazerAPI, store: Store) -> None:
        self.analysis_client = analysis_client
        self.store = store

    def get_status_summary(self, order_id: int) -> OrderSummary:
        return self.get_status_summaries([order_id])[0]

    def get_status_summaries(self, order_ids: list[int]) -> list[OrderSummary]:
        orders: list[Order] = self.store.get_orders_by_ids(order_ids)
        analysis_summaries: list[AnalysisSummary] = self.analysis_client.get_summaries(order_ids)
        return create_summaries(orders=orders, analysis_summaries=analysis_summaries)
