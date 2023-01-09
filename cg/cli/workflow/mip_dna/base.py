"""Commands to start MIP rare disease DNA workflow"""

import logging

import click
from cg.cli.workflow.commands import (
    ensure_flowcells_ondisk,
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


mip_dna.add_command(config_case)
mip_dna.add_command(ensure_flowcells_ondisk)
mip_dna.add_command(link)
mip_dna.add_command(panel)
mip_dna.add_command(resolve_compression)
mip_dna.add_command(run)
mip_dna.add_command(start)
mip_dna.add_command(start_available)
mip_dna.add_command(store)
mip_dna.add_command(store_available)
