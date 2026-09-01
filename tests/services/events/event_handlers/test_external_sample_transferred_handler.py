from unittest.mock import create_autospec

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_sample_transferred_handler


def test_handle_success():
    # GIVEN a CG config
    config: CGConfig = create_autospec(CGConfig)

    # GIVEN a valid event payload
    event_payload = {
        "statusdb.sample_internal_id": "ACC123",
        "cluster_location": "/path/to/home",
        "transfer_completed_at": "2026-08-31T14:41:00",
    }

    # WHEN calling handle
    external_sample_transferred_handler.handle(config=config, event_payload=event_payload)

    # THEN the external sample transferred_at was set
    # THEN a housekeeper bundle and version was created for the sample
    # THEN all sequencing files were added to the bundle
    # THEN an event was published saying the sample was stored

    pass
