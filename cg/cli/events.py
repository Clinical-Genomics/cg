import asyncio

import rich_click as click

from cg.models.cg_config import CGConfig
from cg.services.events import upload_handler
from cg.services.events.event_listener import EventListener


@click.command("listen", hidden=True)
@click.pass_obj
def listen(config: CGConfig):
    listener = EventListener(config.nats)
    listener.register(
        f"{config.nats.stream}.upload.completed", upload_handler.completed(config.status_db)
    )
    asyncio.run(listener.listen())
