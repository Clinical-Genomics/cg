import logging

import click
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flowcell
from cg.cli.demultiplex.sample_sheet import sample_sheet_commands
from cg.models.cg_config import CGConfig
from click import Context

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def demultiplex(context: CGConfig):
    """Command group for the demultiplex commands"""
    context.meta_apis["demultiplex_api"] = DemultiplexingAPI(config=context.obj)


demultiplex.add_command(demultiplex_flowcell)
demultiplex.add_command(demultiplex_all)
demultiplex.add_command(sample_sheet_commands)
