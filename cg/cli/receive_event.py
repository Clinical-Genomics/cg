import json
import logging

import click

from cg.models.cg_config import CGConfig
from cg.services.events import event_dispatching

LOG = logging.getLogger(__name__)


@click.command("receive-event", hidden=True)
@click.argument("event-name", required=True)
@click.option("--event-payload")
@click.pass_obj
def receive_event(config: CGConfig, event_name: str, event_payload: str | None):
    """Receive an event and dispatch it to the appropriate handler."""
    if not event_payload:
        LOG.warning(f"Received event {event_name} with no payload, skipping dispatch.")
        return
    parsed_payload: dict = json.loads(event_payload)
    event_dispatching.dispatch(config=config, event_name=event_name, event_payload=parsed_payload)
    config.status_db.commit_to_store()
