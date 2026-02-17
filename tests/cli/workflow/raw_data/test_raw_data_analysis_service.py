from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.tb.api import TrailblazerAPI
from cg.cli.workflow.raw_data.raw_data_service import RawDataAnalysisService
from cg.constants.constants import Workflow
from cg.constants.priority import Priority, TrailblazerPriority
from cg.constants.tb import AnalysisType
from cg.store.models import Analysis, Case, Order
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.mark.freeze_time
def test_store_analysis():
    raw_data_case_id = "raw_data_case_id"

    case: Case = create_autospec(
        Case,
        id=1,
        internal_id=raw_data_case_id,
        latest_ticket="ticket_2",
        latest_order=create_autospec(Order, id="123"),
        priority=Priority.standard,
    )

    new_analysis = create_autospec(Analysis)

    store: TypedMock[Store] = create_typed_mock(Store)
    store.as_type.get_case_by_internal_id = Mock(return_value=case)
    store.as_type.add_analysis = Mock(return_value=new_analysis)
    store.as_type.session = Mock()

    trailblazer_api = create_autospec(TrailblazerAPI)

    raw_data_analysis_service = RawDataAnalysisService(
        store=store.as_type, trailblazer_api=trailblazer_api
    )

    raw_data_analysis_service.store_analysis(case_id=raw_data_case_id)

    store.as_mock.add_analysis.assert_called_once_with(
        case_id=1,
        completed_at=datetime.now(),
        primary=True,
        started_at=datetime.now(),
        workflow=Workflow.RAW_DATA,
    )
    store.as_mock.session.add.assert_called_once_with(new_analysis)
    store.as_mock.session.commit.assert_called_once()

    trailblazer_api.add_pending_analysis.assert_called_once_with(
        analysis_type=AnalysisType.OTHER,
        case_id=raw_data_case_id,
        config_path="",
        order_id="123",
        out_dir="",
        priority=TrailblazerPriority.NORMAL,
        ticket="ticket_2",
        workflow=Workflow.RAW_DATA,
    )


def test_store_analysis_no_trailblazer_analysis_created():
    raw_data_case_id = "raw_data_case_id"

    case: Case = create_autospec(
        Case,
        id=1,
        internal_id=raw_data_case_id,
        latest_ticket="ticket_2",
        latest_order=create_autospec(Order, id="123"),
        priority=Priority.standard,
    )

    new_analysis = create_autospec(Analysis)

    store: TypedMock[Store] = create_typed_mock(Store)
    store.as_type.get_case_by_internal_id = Mock(return_value=case)
    store.as_type.add_analysis = Mock(return_value=new_analysis)
    store.as_type.session = Mock()

    trailblazer_api = create_autospec(TrailblazerAPI)
    trailblazer_api.add_pending_analysis = Mock(side_effect=Exception)

    raw_data_analysis_service = RawDataAnalysisService(
        store=store.as_type, trailblazer_api=trailblazer_api
    )
    with pytest.raises(Exception):
        raw_data_analysis_service.store_analysis(case_id=raw_data_case_id)

    store.as_mock.add_analysis.assert_not_called()
    store.as_mock.session.commit.assert_not_called()
