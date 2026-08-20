import logging
from typing import Callable

from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


def handle(config: CGConfig, event_name: str, data: dict):
    # 1. Look if there is a registered handler for the event name
    # 2. If there is, call the handler with the config and data
    # 3. Otherwise, log

    event_handlers: dict[str, Callable] = {"existing_event": _existing_event_handler}
    handler: Callable | None = event_handlers.get(event_name)
    if handler:
        handler(config=config, data=data)
    else:
        LOG.info(f"No handler for event {event_name}")


def _existing_event_handler(config: CGConfig, data: dict):
    pass
