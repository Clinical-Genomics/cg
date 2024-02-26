from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.summary import OrderStatusSummary
from cg.services.orders.order_status_service.utils import create_order_summaries, update_summaries
from cg.store.models import Order
from cg.store.store import Store


class OrderStatusService:
    def __init__(self, analysis_client: TrailblazerAPI, store: Store) -> None:
        self.analysis_client = analysis_client
        self.store = store

    def get_status_summaries(self, order_ids: list[int]) -> list[OrderStatusSummary]:
        orders: list[Order] = self.store.get_orders_by_ids(order_ids)
        summaries: list[OrderStatusSummary] = create_order_summaries(orders)
        analysis_summaries: list[AnalysisSummary] = self.analysis_client.get_summaries(order_ids)
        update_summaries(order_summaries=summaries, analysis_summaries=analysis_summaries)
        return summaries
