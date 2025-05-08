from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.store.models import Case


def test_get_cases_ready_for_analysis(balsamic_analysis_api: BalsamicAnalysisAPI):

    # GIVEN a balsamic_context with 1 case that is ready for analysis

    # WHEN running the command
    cases_to_analyse: list[Case] = balsamic_analysis_api.get_cases_ready_for_analysis()

    # THEN only 1 case is retrieved
    assert len(cases_to_analyse) == 1


def test_get_cases_ready_for_analysis_with_limit(balsamic_analysis_api: BalsamicAnalysisAPI):
    # GIVEN a balsamic_context with 1 case that is ready for analysis

    # WHEN running the command with limit=0
    cases_to_analyse: list[Case] = balsamic_analysis_api.get_cases_ready_for_analysis(limit=0)

    # THEN no case is retrieved
    assert len(cases_to_analyse) == 0
