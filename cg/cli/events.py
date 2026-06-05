import asyncio
import os

import rich_click as click

from cg.models.cg_config import CGConfig
from cg.services.events import upload_handler
from cg.services.events.event_listener import EventListener
from cg.services.events.upload_handler import ANALYSIS_UPLOADED_SUBJECT
from cg.store.database import initialize_database
from cg.store.store import Store


@click.command("listen", hidden=True)
@click.pass_obj
def listen(config: CGConfig):
    listener = EventListener(config.nats)

    initialize_database(os.environ["CG_SQL_DATABASE_URI"])
    status_db = Store()

    listener.register(
        f"{config.nats.stream}.{ANALYSIS_UPLOADED_SUBJECT}",
        upload_handler.completed(status_db),
    )
    asyncio.run(listener.listen())
