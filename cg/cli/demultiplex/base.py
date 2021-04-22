import logging

import click
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flowcell
from cg.cli.demultiplex.sample_sheet import sample_sheet_commands

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def demultiplex():
    """Command group for the demultiplex commands"""
    LOG.info("Running CG demultiplex")


demultiplex.add_command(demultiplex_flowcell)
demultiplex.add_command(demultiplex_all)
demultiplex.add_command(sample_sheet_commands)
