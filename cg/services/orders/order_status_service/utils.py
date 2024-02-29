from enum import Enum
from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_status_service.dto.order_status_summary import OrderSummary
from cg.store.models import Case, Order


def create_summaries(
    orders: list[Order], analysis_summaries: list[AnalysisSummary]
) -> list[OrderSummary]:
    summaries: list[OrderSummary] = []
    for order in orders:
        summary: OrderSummary = create_order_summary(order)
        summaries.append(summary)
    add_analysis_summaries(order_summaries=summaries, analysis_summaries=analysis_summaries)
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


class CaseStatus(Enum):
    SEQUENCING = 1
    LAB_PREPARATION = 2
    OTHER = 3


def create_order_summary(order: Order) -> OrderSummary:
    in_sequencing: int = 0
    in_preparation: int = 0

    for case in order.cases:
        status: CaseStatus = get_case_status(case)
        if status == CaseStatus.SEQUENCING:
            in_sequencing += 1
        if status == CaseStatus.LAB_PREPARATION:
            in_preparation += 1

    return OrderSummary(
        order_id=order.id,
        total=len(order.cases),
        in_sequencing=in_sequencing,
        in_lab_preparation=in_preparation,
    )


def get_case_status(case: Case):
    """
    A case is in lab preparation if at least one sample is not prepared yet.
    A case is in sequencing if all samples have been prepared and at least one sample is in sequencing.
    """
    samples_in_sequencing = False
    for sample in case.samples:
        if sample.prepared_at is None:
            return CaseStatus.LAB_PREPARATION
        if sample.last_sequenced_at is None:
            samples_in_sequencing = True
    return CaseStatus.SEQUENCING if samples_in_sequencing else CaseStatus.OTHER
