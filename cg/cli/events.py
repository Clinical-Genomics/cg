import asyncio

import rich_click as click

from cg.models.cg_config import CGConfig
from cg.services.events.event_listener import EventListener


@click.command("listen", hidden=True)
@click.pass_obj
def listen(config: CGConfig):
    listener = EventListener(config.nats)
    listener.register("cg.upload.completed", lambda msg: click.echo(f"Received message: {msg}"))
    asyncio.run(listener.listen())
