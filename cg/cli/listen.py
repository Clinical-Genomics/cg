"""Standalone listen command."""

import asyncio
import logging
import sys

import coloredlogs
import rich_click as click

from cg.apps.tb import TrailblazerAPI
from cg.cli.utils import LOG_LEVELS
from cg.server.app_config import AppConfig
from cg.services.events import upload_handler
from cg.services.events.event_listener import EventListener
from cg.services.events.upload_handler import ANALYSIS_UPLOADED_SUBJECT
from cg.store.database import initialize_database
from cg.store.store import Store

LOG = logging.getLogger(__name__)

pass_app_config = click.make_pass_decorator(AppConfig, ensure=True)


@click.command("listen")
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(LOG_LEVELS),
    default="INFO",
    help="lowest level to log at",
)
@click.option("--verbose", is_flag=True, help="Show full log information, time stamp etc")
@pass_app_config
def listen(app_config: AppConfig, log_level: str, verbose: bool):
    """Listen for incoming event messages."""
    if verbose:
        log_format = "%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s"
    else:
        log_format = "%(message)s" if sys.stdout.isatty() else None
    coloredlogs.install(level=log_level, fmt=log_format)

    trailblazer_api = TrailblazerAPI(config=_trailblazer_config_from_config(app_config))
    LOG.debug(f"{_trailblazer_config_from_config(app_config)}")

    listener = EventListener(
        nats_server=app_config.nats_server,
        nats_stream=app_config.nats_stream,
        listener_ca_cert_path=app_config.listener_ca_cert_path,
        listener_client_cert_path=app_config.listener_client_cert_path,
        listener_client_key_path=app_config.listener_client_key_path,
        listener_token_path=app_config.listener_token_path,
    )
    LOG.info("EventListener initialized with server")
    LOG.info("These are the NATS configuration variables:\n")
    LOG.info(f"{listener.server}")
    LOG.info(f"{listener.stream}")
    LOG.info(f"{listener.ca_cert_path}")
    LOG.info(f"{listener.client_cert}")
    LOG.info(f"{listener.client_key}")
    LOG.debug(f"{listener.token}")

    initialize_database(app_config.cg_sql_database_uri)
    status_db = Store()
    LOG.info(f"Database initialized with URI: {app_config.cg_sql_database_uri}")
    LOG.debug(f"{status_db.__repr__()}")

    # TODO: register the stream and run the listener
    # listener.register(
    #     f"{app_config.nats_stream}.{ANALYSIS_UPLOADED_SUBJECT}",
    #     upload_handler.completed(status_db=status_db, trailblazer_api=trailblazer_api),
    # )
    # asyncio.run(listener.listen())


def _trailblazer_config_from_config(app_config: AppConfig) -> dict[str, dict[str, str]]:
    return {
        "trailblazer": {
            "host": app_config.trailblazer_host,
            "service_account": app_config.trailblazer_service_account,
            "service_account_auth_file": app_config.trailblazer_service_account_auth_file,
        }
    }
