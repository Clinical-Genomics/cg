"""Standalone listen command."""

import logging
import sys

import coloredlogs
import rich_click as click

from cg.cli.utils import LOG_LEVELS
from cg.server.app_config import AppConfig

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

    LOG.info("These are the NATS configuration variables:\n")
    LOG.info(f"{app_config.nats_server}")
    LOG.info(f"{app_config.nats_binary_path}")
    LOG.warning(f"{app_config.nats_stream}")
    LOG.info(f"{app_config.listener_client_cert_path}")
    LOG.info(f"{app_config.listener_client_key_path}")
    LOG.info(f"{app_config.listener_ca_cert_path}")
    LOG.debug(f"{app_config.listener_token_path}")
    LOG.debug(f"{app_config.trailblazer_host}")
    LOG.info(f"{app_config.trailblazer_service_account}")
    LOG.debug(f"{app_config.trailblazer_service_account_auth_file}")
