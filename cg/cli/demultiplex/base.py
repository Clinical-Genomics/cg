"""Module for demultiplexing CLI."""
import logging

import click
from cg.cli.demultiplex.add import add_flow_cell_cmd, select_project_cmd
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flow_cell, delete_flow_cell
from cg.cli.demultiplex.finish import finish_group
from cg.cli.demultiplex.report import create_report_cmd
from cg.cli.demultiplex.sample_sheet import sample_sheet_commands

LOG = logging.getLogger(__name__)


@click.group(name="demultiplex")
def demultiplex_cmd_group():
    """Command group for the demultiplex CLI."""
    LOG.info("Running cg demultiplex.")


demultiplex_cmd_group: click.Group
for sub_cmd in [
    add_flow_cell_cmd,
    create_report_cmd,
    delete_flow_cell,
    demultiplex_flow_cell,
    demultiplex_all,
    finish_group,
    sample_sheet_commands,
    select_project_cmd,
]:
    demultiplex_cmd_group.add_command(sub_cmd)
