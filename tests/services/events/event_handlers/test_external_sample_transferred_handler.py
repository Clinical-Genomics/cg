from unittest.mock import create_autospec

from cg.models.cg_config import CGConfig


def test_handle():
    # GIVEN a CG config
    config: CGConfig = create_autospec(CGConfig)

    # GIVEN a valid event payload
    # TODO cg -> statusdb
    event_payload = {
        "cg.sample_internal_id": "ACC123",
        "cluster_location": "/path/to/home",
        "transfer_completed_at": "2026-08-31T14:41:00",
    }

    # WHEN calling handle

    # THEN
    pass
