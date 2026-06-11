import asyncio
import os

import rich_click as click

from cg.apps.tb import TrailblazerAPI
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

    trailblazer_api = TrailblazerAPI(config=_trailblazer_config_from_env())

    listener.register(
        f"{config.nats.stream}.{ANALYSIS_UPLOADED_SUBJECT}",
        upload_handler.completed(store=status_db, trailblazer_api=trailblazer_api),
    )
    asyncio.run(listener.listen())


def _trailblazer_config_from_env() -> dict[str, dict[str, str]]:
    return {
        "trailblazer": {
            "host": os.environ["TRAILBLAZER_HOST"],
            "service_account": os.environ["TRAILBLAZER_SERVICE_ACCOUNT"],
            "service_account_auth_file": os.environ["TRAILBLAZER_SERVICE_ACCOUNT_AUTH_FILE"],
        }
    }
