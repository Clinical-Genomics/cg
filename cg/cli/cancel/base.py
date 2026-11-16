import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def cancel():
    """Cancel object in Statusdb."""
    LOG.info("Running CG cancel")
