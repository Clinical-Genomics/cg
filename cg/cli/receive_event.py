import json

import click

from cg.models.cg_config import CGConfig
from cg.services.events import event_handler


@click.command("receive-event", hidden=True)
@click.argument("event-name", required=True)
@click.option("--data")
@click.pass_obj
def receive_event(config: CGConfig, event_name: str, data: str | None):
    if not data:
        return
    parsed_data: dict = json.loads(data)
    event_handler.handle(config=config, event_name=event_name, data=parsed_data)
