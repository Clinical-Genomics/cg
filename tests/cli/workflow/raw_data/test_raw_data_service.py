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


@pytest.mark.freeze_time
def test_store_analysis():
    case: Case = create_autospec(
        Case, id=666, priority=Priority.express, internal_id="the_best_case"
    )

    #
    trailblazer_api: TrailblazerAPI = create_autospec(
        TrailblazerAPI,
    )
    session: Session = create_autospec(Session)

    store: Store = create_autospec(Store, session=session)
    store.get_case_by_internal_id = Mock(return_value=case)

    raw_data_analysis_service = RawDataAnalysisService(store=store, trailblazer_api=trailblazer_api)

    #

    raw_data_analysis_service.store_analysis(case_id=case.internal_id)

    store.add_analysis.assert_called_once_with(
        workflow=Workflow.RAW_DATA,
        completed_at=datetime.now(),
        primary=True,
        started_at=datetime.now(),
        case_id=666,
    )

    session.add.assert_called_once()
    session.commit.assert_called_once()
