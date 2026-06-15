from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.tb.api import TrailblazerAPI
from cg.services.events.upload_handler import completed
from cg.store.models import Analysis, Case
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_completed_success():
    # GIVEN a message with an existing analysis id and a date
    message = {"cg.analysis_id": 1, "uploaded_at": "2026-06-02T11:14:52Z"}

    # GIVEN a store with an analysis
    store: TypedMock[Store] = create_typed_mock(Store)
    case: Case = create_autospec(Case, internal_id="case_1")
    analysis: Analysis = create_autospec(Analysis, case=case)

    store.as_type.get_analysis_by_entry_id = Mock(return_value=analysis)

    # GIVEN the trailblazer api is available
    trailblazer_api = create_autospec(TrailblazerAPI)

    # WHEN a completed message is received
    completed_handler = completed(status_db=store.as_type, trailblazer_api=trailblazer_api)
    completed_handler(message)

    # THEN the analysis uploaded_at should have been updated
    expected_date = datetime(year=2026, month=6, day=2, hour=11, minute=14, second=52)
    store.as_mock.update_analysis_uploaded_at.assert_called_once_with(
        analysis_id=1, uploaded_at=expected_date
    )

    # THEN the analysis should have been set as uploaded in Trailblazer
    trailblazer_api.set_analysis_uploaded.assert_called_once_with(
        case_id="case_1", uploaded_at=expected_date
    )


def test_completed_missing_analysis():
    # GIVEN a message with a non-existing analysis id and a date
    message = {"cg.analysis_id": 999, "uploaded_at": "2026-06-02T11:14:52Z"}

    # GIVEN a store
    store = create_autospec(Store)
    store.update_analysis_uploaded_at = Mock(side_effect=Exception)

    # WHEN a completed message is received
    # THEN it lets the exception propagate
    completed_handler = completed(status_db=store, trailblazer_api=create_autospec(TrailblazerAPI))
    with pytest.raises(Exception):
        completed_handler(message)
