from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.dto.order_status_summary import OrderSummary
from cg.services.orders.order_status_service.dto.case_status_summary import CaseSummary
from cg.store.models import Case, Order


def create_status_summaries(orders: list[Order]) -> list[OrderSummary]:
    summaries: list[OrderSummary] = []
    for order in orders:
        case_count: int = get_total_cases_in_order(order)
        summary = OrderSummary(order_id=order.id, total=case_count)
        summaries.append(summary)
    return summaries


def add_analysis_summaries(
    order_summaries: list[OrderSummary],
    analysis_summaries: list[AnalysisSummary],
) -> None:
    order_summary_map = {summary.order_id: summary for summary in order_summaries}
    for analysis_summary in analysis_summaries:
        order_summary = order_summary_map[analysis_summary.order_id]
        order_summary.delivered = analysis_summary.delivered
        order_summary.running = analysis_summary.running
        order_summary.cancelled = analysis_summary.cancelled
        order_summary.failed = analysis_summary.failed


def add_case_summaries(
    order_summaries: list[OrderSummary],
    case_summaries: list[CaseSummary],
) -> None:
    order_summary_map = {summary.order_id: summary for summary in order_summaries}
    for case_summary in case_summaries:
        order_summary = order_summary_map[case_summary.order_id]
        order_summary.in_sequencing = case_summary.in_sequencing
        order_summary.in_preparation = case_summary.in_preparation


def get_total_cases_in_order(order: Order) -> int:
    return len(order.cases)


def create_case_status_summaries(orders: list[Order]) -> list[CaseSummary]:
    summaries: list[CaseSummary] = []
    for order in orders:
        summary: CaseSummary = get_case_status_summary(order)
        summaries.append(summary)
    return summaries


def get_case_status_summary(order: Order) -> CaseSummary:
    in_sequencing: int = get_cases_with_samples_in_sequencing_count(order)
    in_preparation: int = get_cases_with_samples_in_preparation_count(order)
    return CaseSummary(
        order_id=order.id,
        in_sequencing=in_sequencing,
        in_preparation=in_preparation,
    )


def get_cases_with_samples_in_sequencing_count(order: Order) -> int:
    sequencing_count: int = 0
    for case in order.cases:
        if has_samples_in_sequencing(case):
            sequencing_count += 1
    return sequencing_count


def has_samples_in_sequencing(case: Case) -> int:
    for sample in case.samples:
        if not sample.last_sequenced_at:
            return True


def get_cases_with_samples_in_preparation_count(order: Order) -> int:
    preparation_count: int = 0
    for case in order.cases:
        if has_samples_in_preparation(case):
            preparation_count += 1
    return preparation_count


def has_samples_in_preparation(case: Case) -> int:
    for sample in case.samples:
        if not sample.prepared_at:
            return True
