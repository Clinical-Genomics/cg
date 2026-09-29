from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy import Case

from cg.apps.tb.api import TrailblazerAPI
from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import analysis_uploaded_handler
from cg.store.models import Analysis
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_completed_success():
    # GIVEN an event payload with an existing analysis id and a date
    payload = {"cg.analysis_id": 1, "uploaded_at": "2026-06-02T11:14:52"}

    # GIVEN a store with an analysis
    store: TypedMock[Store] = create_typed_mock(Store)
    case: Case = create_autospec(Case, internal_id="case_1")
    analysis: Analysis = create_autospec(Analysis, case=case)

    store.as_type.get_analysis_by_entry_id_strict = Mock(return_value=analysis)

    # GIVEN the trailblazer api is available
    trailblazer_api = create_autospec(TrailblazerAPI)

    # GIVEN a cg config
    cg_config = create_autospec(CGConfig, status_db=store.as_type, trailblazer_api=trailblazer_api)

    # WHEN a completed event is handled
    analysis_uploaded_handler.handle(config=cg_config, event_payload=payload)

    # THEN the analysis uploaded_at should have been updated
    expected_date = datetime(year=2026, month=6, day=2, hour=11, minute=14, second=52)
    assert analysis.uploaded_at == expected_date

    # THEN the analysis should have been set as uploaded in Trailblazer
    trailblazer_api.set_analysis_uploaded.assert_called_once_with(
        case_id="case_1", uploaded_at=expected_date
    )


def test_completed_missing_analysis():
    # GIVEN a payload with a non-existing analysis id and a date
    payload = {"cg.analysis_id": 999, "uploaded_at": "2026-06-02T11:14:52Z"}

    # GIVEN a store
    store = create_autospec(Store)
    store.get_analysis_by_entry_id_strict = Mock(side_effect=Exception("No analysis found"))

    # GIVEN a cg config
    cg_config = create_autospec(CGConfig, status_db=store)

    # WHEN a completed event is handled
    # THEN the exception is propagated
    with pytest.raises(Exception):
        analysis_uploaded_handler.handle(config=cg_config, event_payload=payload)
