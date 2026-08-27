from unittest.mock import Mock, create_autospec

from cg.models.cg_config import CGConfig
from cg.services.events import event_dispatching


def test_dispatch_existing_handler():
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
    )

    # GIVEN an event payload
    event_payload = {"key": "value"}

    # GIVEN a dict of event handlers
    registered_event_handler = Mock()
    event_handlers: dict = {"existing_event": registered_event_handler}

    # WHEN calling dispatch
    event_dispatching.dispatch(
        config=cg_config,
        event_name="existing_event",
        event_payload=event_payload,
        event_handlers=event_handlers,
    )

    # THEN the correct handler was called
    registered_event_handler.assert_called_once_with(config=cg_config, event_payload=event_payload)


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
