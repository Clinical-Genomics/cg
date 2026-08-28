import logging
from typing import Callable

from cg.models.cg_config import CGConfig
from cg.services.events.event_handlers import external_sample_uploaded_handler

LOG = logging.getLogger(__name__)


EVENT_HANDLERS: dict[str, Callable] = {
    "external.customer_uploaded_sample": external_sample_uploaded_handler.handle
}


def dispatch(
    config: CGConfig, event_name: str, event_payload: dict, event_handlers: dict = EVENT_HANDLERS
):
    """
    Select the appropriate handler for the given event name and call it with the provided payload.
    """
    handler_function: Callable | None = event_handlers.get(event_name)
    if handler_function:
        LOG.debug(f"Dispatching event {event_name} to handler {handler_function.__name__}")
        handler_function(config=config, event_payload=event_payload)
    else:
        LOG.info(f"No handler for event {event_name}")
