from datetime import datetime
from unittest.mock import create_autospec

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_sample_uploaded_handler
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_handle_triggers_download_success():
    # GIVEN a CGConfig
    status_db: TypedMock[Store] = create_typed_mock(Store)
    cg_config: CGConfig = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN some data
    data = {
        "customer": "cust000",
        "sample_name": "sample_name",
        "customer_uploaded_at": "2026-06-02T11:14:52Z",
    }

    # GIVEN that the sample should be downloaded
    # TODO: Set this up

    # WHEN calling handle with a CGConfig and some data
    external_sample_uploaded_handler.handle(config=cg_config, data=data)

    # THEN the provided data should have been added to the database
    status_db.as_mock.add_external_sample.assert_called_once_with(
        customer_internal_id="cust000",
        sample_name="sample_name",
        customer_uploaded_at=datetime(year=2026, month=6, day=2, hour=11, minute=14, second=52),
    )

    # THEN the sample should be downloaded
    # TODO: Add assertion
