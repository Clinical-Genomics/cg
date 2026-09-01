from datetime import datetime
from unittest.mock import Mock, create_autospec

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_sample_transferred_handler
from cg.store.models import Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_handle_success():
    # GIVEN a CG config
    status_db: TypedMock[Store] = create_typed_mock(Store)
    sample: Sample = create_autospec(Sample, customer_id=1)
    sample.name = "sample-name"
    status_db.as_type.get_sample_by_internal_id_strict = Mock(return_value=sample)
    config: CGConfig = create_autospec(CGConfig, status_db=status_db.as_type)

    # GIVEN a valid event payload
    event_payload = {
        "statusdb.sample_internal_id": "ACC123",
        "cluster_location": "/path/to/home",
        "transfer_completed_at": "2026-08-31T14:41:00",
    }

    # WHEN calling handle
    external_sample_transferred_handler.handle(config=config, event_payload=event_payload)

    # THEN the external sample transferred_at was set
    status_db.as_mock.update_external_sample.assert_called_once_with(
        sample_name="sample-name", customer_id=1, transferred_at=datetime.now()
    )

    # THEN a housekeeper bundle and version was created for the sample
    # THEN all sequencing files were added to the bundle
    # THEN an event was published saying the sample was stored
