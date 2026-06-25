"""Code for store part of CLI."""

import logging

import rich_click as click

from cg.cli.store.store import store_qc_metrics
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def store(context: CGConfig):
    """Command for storing files."""
    LOG.info("Running CG store command")


store.add_command(store_qc_metrics)
