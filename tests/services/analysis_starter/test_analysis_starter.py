from unittest.mock import create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.exc import AnalysisNotReadyError, AnalysisRunningError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.analysis_starter.service import AnalysisStarter
from cg.store.models import Case
from cg.store.store import Store


@pytest.mark.parametrize(
    "error, expected_exit",
    [
        (None, True),
        (AnalysisNotReadyError, True),
        (AnalysisRunningError, False),
        (Exception, False),
    ],
    ids=["Success", "Fastqs missing", "Analysis ongoing", "General error"],
)
def test_microsalt_analysis_starter_start_available_error_handling(
    cg_context: CGConfig, mocker: MockerFixture, error: type[Exception], expected_exit: bool
):
    # GIVEN an AnalysisStarter
    analysis_starter: AnalysisStarter = AnalysisStarterFactory(
        cg_context
    ).get_analysis_starter_for_workflow(Workflow.MICROSALT)

    # GIVEN that the start exits with a given behaviour
    mocker.patch.object(Store, "get_cases_to_analyze", return_value=[create_autospec(Case)])
    mocker.patch.object(AnalysisStarter, "start", return_value=None, side_effect=error)

    # WHEN starting all available cases
    succeeded: bool = analysis_starter.start_available()

    # THEN it should have exited with the expected value
    assert succeeded == expected_exit
