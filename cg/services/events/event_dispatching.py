import logging
from typing import Protocol

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_sample_uploaded_handler

LOG = logging.getLogger(__name__)


class EventHandler(Protocol):
    def __call__(self, config: CGConfig, event_payload: dict) -> None: ...


EVENT_HANDLERS: dict[str, EventHandler] = {
    "external.customer_uploaded_sample": external_sample_uploaded_handler.handle
}


def dispatch(
    config: CGConfig,
    event_name: str,
    event_payload: dict,
    event_handlers: dict[str, EventHandler] = EVENT_HANDLERS,
):
    """Select the appropriate handler for the given event name and call it with the provided data."""
    handle_function: EventHandler | None = event_handlers.get(event_name)
    if handle_function:
        handle_function(config=config, event_payload=event_payload)
    else:
        LOG.info(f"No handler for event {event_name}")
