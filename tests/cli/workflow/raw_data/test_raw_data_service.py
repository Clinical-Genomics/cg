from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.cli.workflow.raw_data.raw_data_service import RawDataAnalysisService
from cg.constants import Priority
from cg.constants.constants import Workflow
from cg.store.models import Case
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.mark.freeze_time
def test_store_analysis():
    # GIVEN a raw data case
    case: Case = create_autospec(
        Case, id=666, priority=Priority.express, internal_id="the_best_case"
    )

    # GIVEN that a pending analysis can be created in trailblazer
    trailblazer_api: TrailblazerAPI = create_autospec(
        TrailblazerAPI,
    )
    trailblazer_api.add_pending_analysis = Mock(
        return_value=TrailblazerAnalysis(
            case_id="the_best_case",
            id=67,
            logged_at="1992-12-13",  # type: ignore pydantic model
            started_at="1992-12-13",  # type: ignore pydantic model
            completed_at=None,
            out_dir=Path("great_path"),
            config_path=Path("great_config_path"),
        )
    )

    # GIVEN the case can be fetched from statusdb
    store: TypedMock[Store] = create_typed_mock(Store)
    store.as_type.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN a raw data analysis service
    raw_data_analysis_service = RawDataAnalysisService(
        store=store.as_type, trailblazer_api=trailblazer_api
    )

    # WHEN storing the analysis of the raw data case
    raw_data_analysis_service.store_analysis(case_id=case.internal_id)

    # THEN an analysis is added to statusdb
    store.as_mock.add_analysis.assert_called_once_with(
        workflow=Workflow.RAW_DATA,
        completed_at=datetime.now(),
        primary=True,
        started_at=datetime.now(),
        case_id=666,
        trailblazer_id=67,
    )
    store.as_mock.add_item_to_store.assert_called_once()
    store.as_mock.commit_to_store.assert_called_once()
