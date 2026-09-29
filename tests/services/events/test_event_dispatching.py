from datetime import datetime
from unittest.mock import Mock, create_autospec

from cg.models.cg_config import CGConfig
from cg.services.events import event_dispatching


def test_dispatch_existing_handler():
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
    )

    # GIVEN an event payload
    event_payload: dict = {"key": "value"}

    # GIVEN event metadata
    event_metadata: dict = {
        "sequence": {"consumer": 2, "stream": 1},
        "num_pending": 0,
        "num_delivered": 2,
        "timestamp": "2026-09-29T11:32:12",
        "stream": "cg-local-dev",
        "consumer": "cluster-consumer",
    }

    # GIVEN a dict of event handlers
    registered_event_handler = Mock()
    event_handlers: dict = {"existing_event": registered_event_handler}

    # WHEN calling dispatch
    event_dispatching.dispatch(
        config=cg_config,
        event_name="existing_event",
        event_payload=event_payload,
        event_handlers=event_handlers,
        event_metadata=event_metadata,
    )

    # THEN the correct handler was called
    registered_event_handler.assert_called_once_with(
        config=cg_config,
        event_payload=event_payload,
        event_metadata=EventMetadata(
            sequence=EventSequence(consumer=2, stream=1),
            num_pending=0,
            num_delivered=2,
            timestamp=datetime.strptime("2026-09-29T11:32:12", "%Y-%m-%dT%H:%M:%S"),
            stream="cg-local-dev",
            cunsumer="cluster-consumer",
        ),
    )


def test_dispatch_no_handler():
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
    )

    # GIVEN an event payload
    event_payload = {"key": "value"}

    # GIVEN an event name that doesn't have a handler
    event_name = "no-handler-event"

    # WHEN calling dispatch
    # THEN it doesn't raise
    event_dispatching.dispatch(
        config=cg_config, event_name=event_name, event_payload=event_payload, event_handlers={}
    )
