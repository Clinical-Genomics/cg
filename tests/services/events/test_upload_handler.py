from datetime import datetime
from unittest.mock import Mock, create_autospec

from cg.services.events.upload_handler import completed
from cg.store.store import Store


def test_completed_success():
    # GIVEN a message with an existing analysis id and a date
    message = {"cg.analysis_id": 1, "uploaded_at": "2026-06-02T11:14:52Z"}

    # GIVEN a store with an analysis
    store = create_autospec(Store)

    # WHEN a completed message is received
    completed_handler = completed(store)
    completed_handler(message)

    # THEN the analysis uploaded_at should have been updated
    expected_date = datetime(year=2026, month=6, day=2, hour=11, minute=14, second=52)
    store.update_analysis_uploaded_at.assert_called_once_with(
        analysis_id=1, uploaded_at=expected_date
    )


def test_completed_missing_analysis():
    # GIVEN a message with a non-existing analysis id and a date
    message = {"cg.analysis_id": 999, "uploaded_at": "2026-06-02T11:14:52Z"}

    # GIVEN a store
    store = create_autospec(Store)
    store.update_analysis_uploaded_at = Mock(side_effect=Exception)

    # WHEN a completed message is received
    completed_handler = completed(store)
    completed_handler(message)

    # THEN it should not raise an exception
