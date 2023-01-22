"""CLI support to create config and/or start BALSAMIC """

import logging

import click

from cg.cli.workflow.balsamic.base import (
    config_case,
    run,
    report_deliver,
    store_housekeeper,
    start,
    start_available,
    store,
    store_available,
)
from cg.cli.workflow.commands import link, resolve_compression
from cg.meta.workflow.balsamic_qc import BalsamicQCAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group("balsamic-qc", invoke_without_command=True)
@click.pass_context
def balsamic_qc(context: click.Context):
    """Cancer analysis workflow"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    config = context.obj
    context.obj.meta_apis["analysis_api"] = BalsamicQCAnalysisAPI(
        config=config,
    )


balsamic_qc.add_command(resolve_compression)
balsamic_qc.add_command(link)
balsamic_qc.add_command(config_case)
balsamic_qc.add_command(run)
balsamic_qc.add_command(report_deliver)
balsamic_qc.add_command(store_housekeeper)
balsamic_qc.add_command(start)
balsamic_qc.add_command(start_available)
balsamic_qc.add_command(store)
balsamic_qc.add_command(store_available)
