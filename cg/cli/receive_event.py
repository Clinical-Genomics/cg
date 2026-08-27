import json

import click

from cg.models.cg_config import CGConfig
from cg.services.events import event_dispatching


@click.command("receive-event", hidden=True)
@click.argument("event-name", required=True)
@click.option("--event-payload")
@click.pass_obj
def receive_event(config: CGConfig, event_name: str, event_payload: str | None):
    if not event_payload:
        return
    parsed_payload: dict = json.loads(event_payload)
    event_dispatching.dispatch(config=config, event_name=event_name, event_payload=parsed_payload)
    config.status_db.commit_to_store()
