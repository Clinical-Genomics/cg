from unittest.mock import create_autospec

from pytest_mock import MockerFixture

from cg.models.cg_config import CGConfig
from cg.services.events import event_handler


def test_handle_existing_handler(mocker: MockerFixture):
    # GIVEN a CGConfig
    cg_config: CGConfig = create_autospec(
        CGConfig,
    )

    # GIVEN an event data dictionary
    data = {"key": "value"}

    event_handler_spy = mocker.spy(event_handler, "_existing_event_handler")

    # WHEN calling handle
    event_handler.handle(config=cg_config, event_name="existing_event", data=data)

    # THEN the correct handler was called
    event_handler_spy.assert_called_once_with(config=cg_config, data=data)


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
    event_handler.handle(config=cg_config, event_name=event_name, data=data)
