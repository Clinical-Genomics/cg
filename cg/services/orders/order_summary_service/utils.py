from cg.apps.tb.dto.summary_response import AnalysisSummary
from cg.services.sequencing_qc_service import SequencingQCService
from cg.store.models import Case, Order


def _get_analysis_map(analysis_summaries: list[AnalysisSummary]) -> dict:
    return {summary.order_id: summary for summary in analysis_summaries}


def _is_case_failed_sequencing_qc(case: Case) -> bool:
    return case.are_all_samples_sequenced and not SequencingQCService.case_pass_sequencing_qc(case)


def get_cases_failed_sequencing_qc_count(order: Order, cases_to_exclude: list[str]) -> int:
    cases: list[Case] = order.cases
    return sum(
        1
        for case in cases
        if _is_case_failed_sequencing_qc(case) and case.internal_id not in cases_to_exclude
    )
