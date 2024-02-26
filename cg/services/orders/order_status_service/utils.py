from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.dto.order_status_summary import OrderStatusSummary
from cg.services.orders.order_status_service.dto.case_status_summary import CaseStatusSummary
from cg.store.models import Case, Order


def create_status_summaries(orders: list[Order]) -> list[OrderStatusSummary]:
    summaries: list[OrderStatusSummary] = []
    for order in orders:
        case_count: int = get_total_cases_in_order(order)
        summary = OrderStatusSummary(order_id=order.id, total=case_count)
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


def get_case_status_summaries(orders: list[Order]) -> list[CaseStatusSummary]:
    summaries: list[CaseStatusSummary] = []
    for order in orders:
        summary: CaseStatusSummary = get_case_status_summary(order)
        summaries.append(summary)
    return summaries


def get_case_status_summary(order: Order) -> CaseStatusSummary:
    in_sequencing: int = get_cases_with_samples_in_sequencing_count(order)
    in_preparation: int = get_cases_with_samples_in_preparation_count(order)
    return CaseStatusSummary(
        order_id=order.id,
        in_sequencing=in_sequencing,
        in_preparation=in_preparation,
    )


def get_cases_with_samples_in_sequencing_count(order: Order) -> int:
    in_sequencing_count: int = 0
    for case in order.cases:
        pass
    return in_sequencing_count

def has_samples_in_sequencing(case: Case) -> int:
    pass


def get_cases_with_samples_in_preparation_count(order: Order) -> int:
    pass
