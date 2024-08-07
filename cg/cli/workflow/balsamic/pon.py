"""CLI support to create config and/or start BALSAMIC PON analysis"""

import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.balsamic.base import config_case, run, start
from cg.cli.workflow.commands import link, resolve_compression
from cg.meta.workflow.balsamic_pon import BalsamicPonAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(
    "balsamic-pon",
    invoke_without_command=True,
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.pass_context
def balsamic_pon(context: click.Context):
    """Cancer PON analysis workflow"""

    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None

    config = context.obj
    context.obj.meta_apis["analysis_api"] = BalsamicPonAnalysisAPI(config=config)


balsamic_pon.add_command(resolve_compression)
balsamic_pon.add_command(link)
balsamic_pon.add_command(config_case)
balsamic_pon.add_command(run)
balsamic_pon.add_command(start)
