"""Module for demultiplexing CLI."""
import logging

import click
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flow_cell, delete_flow_cell
from cg.cli.demultiplex.finish import finish_group
from cg.cli.demultiplex.sample_sheet import sample_sheet_commands

LOG = logging.getLogger(__name__)


@click.group(name="demultiplex")
def demultiplex_cmd_group():
    """Command group for the demultiplex CLI."""
    LOG.info("Running cg demultiplex.")


demultiplex_cmd_group: click.Group
for sub_cmd in [
    delete_flow_cell,
    demultiplex_flow_cell,
    demultiplex_all,
    finish_group,
    sample_sheet_commands,
]:
    demultiplex_cmd_group.add_command(sub_cmd)
