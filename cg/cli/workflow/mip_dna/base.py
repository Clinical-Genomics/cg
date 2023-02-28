"""Commands to start MIP rare disease DNA workflow"""

import logging

import click
from cg.cli.workflow.commands import (
    ensure_flow_cells_on_disk,
    link,
    resolve_compression,
    store,
    store_available,
)
from cg.cli.workflow.mip.base import config_case, panel, run, start, start_available
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.analysis import AnalysisAPI

LOG = logging.getLogger(__name__)


@click.group("mip-dna", invoke_without_command=True)
@click.pass_context
def mip_dna(
    context: click.Context,
):
    """Rare disease DNA workflow"""
    AnalysisAPI.get_help(context)

    context.obj.meta_apis["analysis_api"] = MipDNAAnalysisAPI(config=context.obj)


for sub_cmd in [
    config_case,
    ensure_flow_cells_on_disk,
    link,
    panel,
    resolve_compression,
    run,
    start,
    start_available,
    store,
    store_available,
]:
    mip_dna.add_command(sub_cmd)
