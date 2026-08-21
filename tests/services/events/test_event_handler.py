from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig
from cg.services.events import event_handler
from cg.services.events.event_handler import EVENT_HANDLERS
from cg.services.events.event_handlers import external_sample_uploaded_handler


def test_handle_existing_handler():
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
    )

    # GIVEN an event data dictionary
    data = {"key": "value"}

    # GIVEN a dict of event handlers
    registered_event_handler = Mock()
    event_handlers: dict = {"existing_event": registered_event_handler}

    # WHEN calling handle
    event_handler.handle(
        config=cg_config, event_name="existing_event", data=data, event_handlers=event_handlers
    )

    # THEN the correct handler was called
    registered_event_handler.assert_called_once_with(config=cg_config, data=data)


def test_handle_no_handler(mocker: MockerFixture):
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
    )

    # GIVEN an event data dictionary
    data = {"key": "value"}

    # GIVEN an event name that doesn't have a handler
    event_name = "no-handler-event"

    # WHEN calling handle
    # THEN it doesn't raise
    event_handler.handle(config=cg_config, event_name=event_name, data=data, event_handlers={})


def test_handle_sample_uploaded(mocker: MockerFixture):
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(CGConfig)
    data = {"key": "value"}

    handle_spy = mocker.spy(external_sample_uploaded_handler, "handle")
    mocker.patch.dict(
        EVENT_HANDLERS,
        {"external.customer_uploaded_sample": handle_spy},
    )

    # WHEN calling the event handler with an event for external_sample_uploaded_handler
    event_handler.handle(
        config=cg_config,
        event_name="external.customer_uploaded_sample",
        data=data,
    )

    # THEN the correct handler should have been called
    handle_spy.assert_called_once_with(config=cg_config, data=data)
