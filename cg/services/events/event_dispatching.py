import logging
from typing import Protocol

from cg.models.cg_config import CGConfig
from cg.services.events.constants import (
    EXTERNAL_SAMPLE_STORED_SUBJECT,
    EXTERNAL_SAMPLE_TRANSFERRED_SUBJECT,
    EXTERNAL_SAMPLE_UPLOADED_SUBJECT,
    EXTERNAL_SAMPLES_ORDERED_SUBJECT,
)
from cg.services.events.event_handlers import (
    external_sample_stored_handler,
    external_sample_transferred_handler,
    external_sample_uploaded_handler,
    external_samples_ordered_handler,
)

LOG = logging.getLogger(__name__)


class EventHandler(Protocol):
    def __call__(self, config: CGConfig, event_payload: dict) -> None: ...


EVENT_HANDLERS: dict[str, EventHandler] = {
    EXTERNAL_SAMPLE_UPLOADED_SUBJECT: external_sample_uploaded_handler.handle,
    EXTERNAL_SAMPLE_STORED_SUBJECT: external_sample_stored_handler.handle,
    EXTERNAL_SAMPLES_ORDERED_SUBJECT: external_samples_ordered_handler.handle,
    EXTERNAL_SAMPLE_TRANSFERRED_SUBJECT: external_sample_transferred_handler.handle,
}


def dispatch(
    config: CGConfig, event_name: str, event_payload: dict, event_handlers: dict = EVENT_HANDLERS
) -> None:
    """
    Select the appropriate handler for the given event name and call it with the provided payload.
    """
    handler_function: EventHandler | None = event_handlers.get(event_name)
    if handler_function:
        LOG.debug(f"Dispatching event {event_name} to handler {handler_function.__name__}")
        handler_function(config=config, event_payload=event_payload)
    else:
        LOG.info(f"No handler for event {event_name}")
