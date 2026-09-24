"""Standalone listen command."""

import asyncio
import logging
import os
import sys

import coloredlogs
import rich_click as click

from cg.apps.tb import TrailblazerAPI
from cg.cli.utils import LOG_LEVELS
from cg.services.events import upload_handler
from cg.services.events.event_listener import EventListener
from cg.services.events.upload_handler import ANALYSIS_UPLOADED_SUBJECT
from cg.store.database import initialize_database
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("listen", hidden=True)
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(LOG_LEVELS),
    default="INFO",
    help="lowest level to log at",
)
@click.option("--verbose", is_flag=True, help="Show full log information, time stamp etc")
def listen(log_level: str, verbose: bool):
    """Listen for incoming event messages."""
    if verbose:
        log_format = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"
    else:
        log_format = "%(message)s" if sys.stdout.isatty() else None
    coloredlogs.install(level=log_level, fmt=log_format)

    trailblazer_api = TrailblazerAPI(config=_trailblazer_config_from_env())

    nats_stream: str = os.environ["NATS_STREAM"]

    listener = EventListener(
        nats_server=os.environ["NATS_SERVER"],
        nats_stream=nats_stream,
        listener_ca_cert_path=os.environ["LISTENER_CA_CERT_PATH"],
        listener_client_cert_path=os.environ["LISTENER_CLIENT_CERT_PATH"],
        listener_client_key_path=os.environ["LISTENER_CLIENT_KEY_PATH"],
        listener_token_path=os.environ["LISTENER_TOKEN_PATH"],
    )
    LOG.info("Event listener initialized")

    initialize_database(os.environ["CG_SQL_DATABASE_URI"])
    status_db = Store()

    listener.register(
        f"{nats_stream}.{ANALYSIS_UPLOADED_SUBJECT}",
        upload_handler.completed(status_db=status_db, trailblazer_api=trailblazer_api),
    )
    LOG.info(f"Registered handler for subject: {nats_stream}.{ANALYSIS_UPLOADED_SUBJECT}")
    asyncio.run(listener.listen())


def _trailblazer_config_from_env() -> dict[str, dict[str, str]]:
    return {
        "trailblazer": {
            "host": os.environ["TRAILBLAZER_HOST"],
            "service_account": os.environ["TRAILBLAZER_SERVICE_ACCOUNT"],
            "service_account_auth_file": os.environ["TRAILBLAZER_SERVICE_ACCOUNT_AUTH_FILE"],
        }
    }
