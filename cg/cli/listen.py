"""Standalone listen command."""

import logging

import rich_click as click

from cg.server.app_config import AppConfig

pass_app_config = click.make_pass_decorator(AppConfig, ensure=True)

LOG = logging.getLogger(__name__)


@click.command("listen")
@pass_app_config
def listen(app_config: AppConfig):
    """Listen for incoming event messages."""
    # Placeholder while AppConfig-driven listen behavior is implemented.
    LOG.info("These are the configuration variables:\n")
    LOG.info(f"{app_config.freshdesk_url}")
    LOG.info(f"{app_config.freshdesk_environment}")
