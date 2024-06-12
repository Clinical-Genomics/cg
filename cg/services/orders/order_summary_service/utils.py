from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.orders.order_summary_service.dto.case_summary import CaseSummary
from cg.services.orders.order_summary_service.dto.order_summary import OrderSummary
from cg.services.sequencing_qc_service import SequencingQCService
from cg.store.models import Case, Order


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
        summary = create_order_summary(order=order, analysis_summary=analysis, case_summary=case)
        summaries.append(summary)
    return summaries


def create_order_summary(
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
        completed=analysis_summary.completed,
        failed_sequencing_qc=case_summary.failed_sequencing_qc,
    )


def _get_analysis_map(analysis_summaries: list[AnalysisSummary]) -> dict:
    return {summary.order_id: summary for summary in analysis_summaries}


def _get_case_map(case_summaries: list[CaseSummary]) -> dict:
    return {summary.order_id: summary for summary in case_summaries}


def _is_case_failed_sequencing_qc(case: Case) -> bool:
    return case.are_all_samples_sequenced and not SequencingQCService.case_pass_sequencing_qc(case)


def get_cases_failed_sequencing_qc_count(order: Order) -> int:
    cases: list[Case] = order.cases
    return sum(1 for case in cases if _is_case_failed_sequencing_qc(case))
