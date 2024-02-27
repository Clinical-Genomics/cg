from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.dto.case_status_summary import CaseSummary
from cg.services.orders.order_status_service.dto.order_status_summary import OrderSummary
from cg.services.orders.order_status_service.utils import (
    add_case_summaries,
    create_status_summaries,
    create_case_status_summaries,
    add_analysis_summaries,
)
from cg.store.models import Order
from cg.store.store import Store


class OrderStatusService:
    def __init__(self, analysis_client: TrailblazerAPI, store: Store) -> None:
        self.analysis_client = analysis_client
        self.store = store

    def get_status_summaries(self, order_ids: list[int]) -> list[OrderSummary]:
        orders: list[Order] = self.store.get_orders_by_ids(order_ids)
        summaries: list[OrderSummary] = create_status_summaries(orders)
        case_summaries: list[CaseSummary] = create_case_status_summaries(orders)
        analysis_summaries: list[AnalysisSummary] = self.analysis_client.get_summaries(order_ids)
        add_case_summaries(order_summaries=summaries, case_summaries=case_summaries)
        add_analysis_summaries(order_summaries=summaries, analysis_summaries=analysis_summaries)
        return summaries
