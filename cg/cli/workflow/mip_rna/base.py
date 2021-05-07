"""Commands to start MIP rare disease RNA workflow"""

import logging

import click
from cg.cli.workflow.commands import link, resolve_compression, store, store_available
from cg.cli.workflow.mip.base import config_case, panel, run, start, start_available
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group("mip-rna")
@click.pass_context
def mip_rna(context: click.Context):
    """Rare disease RNA workflow"""

    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return

    context.obj.meta_apis["analysis_api"] = MipRNAAnalysisAPI(config=context.obj)


mip_rna.add_command(config_case)
mip_rna.add_command(link)
mip_rna.add_command(panel)
mip_rna.add_command(resolve_compression)
mip_rna.add_command(run)
mip_rna.add_command(start)
mip_rna.add_command(start_available)
mip_rna.add_command(store)
mip_rna.add_command(store_available)
