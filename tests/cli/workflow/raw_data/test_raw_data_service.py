from unittest.mock import create_autospec

from sqlalchemy.orm import Session

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.raw_data.raw_data_service import RawDataAnalysisService
from cg.constants import Priority
from cg.store.models import Case
from cg.store.store import Store


def test_store_analysis():
    case: Case = create_autospec(Case, priority=Priority.express, internal_id="the_best_case")

    #
    trailblazer_api: TrailblazerAPI = create_autospec(
        TrailblazerAPI,
    )
    store: Store = create_autospec(Store, session=create_autospec(Session))
    raw_data_analysis_service = RawDataAnalysisService(store=store, trailblazer_api=trailblazer_api)

    #

    raw_data_analysis_service.store_analysis(case_id=case.internal_id)
