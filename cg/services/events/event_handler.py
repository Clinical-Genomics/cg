import logging
from typing import Callable

from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


EVENT_HANDLERS: dict = {}


def handle(config: CGConfig, event_name: str, data: dict, event_handlers: dict = EVENT_HANDLERS):
    handler: Callable | None = event_handlers.get(event_name)
    if handler:
        handler(config=config, data=data)
    else:
        LOG.info(f"No handler for event {event_name}")
