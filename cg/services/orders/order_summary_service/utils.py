from cg.apps.tb.dto.summary_response import AnalysisSummary


def _get_analysis_map(analysis_summaries: list[AnalysisSummary]) -> dict:
    return {summary.order_id: summary for summary in analysis_summaries}
