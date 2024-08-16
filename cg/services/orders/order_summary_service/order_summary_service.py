from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_summary_service.dto.order_summary import OrderSummary
from cg.services.orders.order_summary_service.utils import _get_analysis_map
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
        analyses: list[AnalysisSummary] = self.analysis_client.get_summaries(order_ids)
        order_summaries = self.create_summaries(orders=orders, analysis_summaries=analyses)
        return order_summaries

    def create_summaries(
        self, orders: list[Order], analysis_summaries: list[AnalysisSummary]
    ) -> list[OrderSummary]:
        order_summaries: list[OrderSummary] = []
        analysis_summary_map: dict = _get_analysis_map(analysis_summaries)
        for order in orders:
            analysis_summary: AnalysisSummary = analysis_summary_map.get(order.id)
            order_summary = self.create_order_summary(order=order, summary=analysis_summary)
            order_summaries.append(order_summary)
        return order_summaries

    def create_order_summary(self, order: Order, summary: AnalysisSummary) -> OrderSummary:
        """Adds statuses inferred from StatusDB data for any cases not included in the provided summary."""
        order_id = order.id
        counted_cases: list[str] = summary.case_ids if summary else []
        not_received: int = self.store.get_case_not_received_count(
            order_id=order_id, cases_to_exclude=counted_cases
        )
        in_preparation: int = self.store.get_case_in_preparation_count(
            order_id=order_id, cases_to_exclude=counted_cases
        )
        in_sequencing: int = self.store.get_case_in_sequencing_count(
            order_id=order_id, cases_to_exclude=counted_cases
        )
        failed_sequencing_qc: int = self.store.get_case_failed_sequencing_count(
            order_id=order_id, cases_to_exclude=counted_cases
        )

        return OrderSummary(
            order_id=order_id,
            total=len(order.cases),
            cancelled=summary.cancelled.count,
            completed=summary.completed.count,
            delivered=summary.delivered.count,
            failed=summary.failed.count,
            failed_sequencing_qc=failed_sequencing_qc,
            in_lab_preparation=in_preparation,
            in_sequencing=in_sequencing,
            not_received=not_received,
            running=summary.running.count,
        )
