from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy.orm import Session

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.raw_data.raw_data_service import RawDataAnalysisService
from cg.constants import Priority
from cg.constants.constants import Workflow
from cg.store.models import Case
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock



@pytest.mark.freeze_time
def test_store_analysis():
    case: Case = create_autospec(
        Case, id=666, priority=Priority.express, internal_id="the_best_case"
    )

    #
    trailblazer_api: TrailblazerAPI = create_autospec(
        TrailblazerAPI,
    )
    session: TypedMock[Session] = create_typed_mock(Session)

    store: TypedMock[Store] = create_typed_mock(Store, session=session.as_type)
    store.as_type.get_case_by_internal_id = Mock(return_value=case)

    raw_data_analysis_service = RawDataAnalysisService(store=store.as_type, trailblazer_api=trailblazer_api)

    #

    raw_data_analysis_service.store_analysis(case_id=case.internal_id)

    store.as_mock.add_analysis.assert_called_once_with(
        workflow=Workflow.RAW_DATA,
        completed_at=datetime.now(),
        primary=True,
        started_at=datetime.now(),
        case_id=666,
        trailblazer_id=67,
    )

    session.as_mock.add.assert_called_once()
    session.as_mock.commit.assert_called_once()
