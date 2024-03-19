from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.dto.case_summary import CaseSummary
from cg.services.orders.order_status_service.dto.order_summary import OrderSummary
from cg.store.models import Order


def create_summaries(
    orders: list[Order],
    analysis_summaries: list[AnalysisSummary],
    case_summaries: list[CaseSummary],
) -> list[OrderSummary]:
    summaries: list[OrderSummary] = []
    analysis_map: dict = _get_analysis_map(analysis_summaries)
    case_map: dict = _get_case_map(case_summaries)

    for order in orders:
        case: CaseSummary = case_map[order.id]
        analysis: AnalysisSummary = analysis_map[order.id]
        summary = get_order_summary(order=order, analysis_summary=analysis, case_summary=case)
        summaries.append(summary)
    return summaries


def get_order_summary(
    order: Order,
    analysis_summary: AnalysisSummary,
    case_summary: CaseSummary,
) -> OrderSummary:
    return OrderSummary(
        order_id=order.id,
        total=len(order.cases),
        in_sequencing=case_summary.in_sequencing,
        in_lab_preparation=case_summary.in_preparation,
        not_received=case_summary.not_received,
        running=analysis_summary.running,
        delivered=analysis_summary.delivered,
        cancelled=analysis_summary.cancelled,
        failed=analysis_summary.failed,
    )


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


def _get_analysis_map(analysis_summaries: list[AnalysisSummary]) -> dict:
    return {summary.order_id: summary for summary in analysis_summaries}


def _get_case_map(case_summaries: list[CaseSummary]) -> dict:
    return {summary.order_id: summary for summary in case_summaries}
