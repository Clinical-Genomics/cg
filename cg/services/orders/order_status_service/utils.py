from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.summary import OrderStatusSummary
from cg.store.models import Order


def create_order_summaries(orders: list[Order]) -> list[OrderStatusSummary]:
    summaries: list[OrderStatusSummary] = []
    for order in orders:
        case_count: int = get_total_cases_in_order(order)
        summary = OrderStatusSummary(total=case_count)
        summaries.append(summary)
    return summaries


def update_summaries(
    order_summaries: list[OrderStatusSummary], analysis_summaries: list[AnalysisSummary]
) -> None:
    order_summary_map = {summary.order_id: summary for summary in order_summaries}
    for analysis_summary in analysis_summaries:
        order_summary = order_summary_map[analysis_summary.order_id]
        order_summary.delivered = analysis_summary.delivered
        order_summary.running = analysis_summary.running
        order_summary.cancelled = analysis_summary.cancelled
        order_summary.failed = analysis_summary.failed


def get_total_cases_in_order(order: Order) -> int:
    return len(order.cases)
