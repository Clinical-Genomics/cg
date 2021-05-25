import logging

import click
from cg.cli.demultiplex.add import add_flowcell_cmd, select_project_cmd
from cg.cli.demultiplex.demux import demultiplex_all, demultiplex_flowcell
from cg.cli.demultiplex.finish import finish_group
from cg.cli.demultiplex.report import create_report_cmd
from cg.cli.demultiplex.sample_sheet import sample_sheet_commands

LOG = logging.getLogger(__name__)


@click.group(name="demultiplex")
def demultiplex_cmd_group():
    """Command group for the demultiplex commands"""
    LOG.info("Running CG demultiplex")


demultiplex_cmd_group: click.Group
demultiplex_cmd_group.add_command(demultiplex_flowcell)
demultiplex_cmd_group.add_command(demultiplex_all)
demultiplex_cmd_group.add_command(sample_sheet_commands)
demultiplex_cmd_group.add_command(add_flowcell_cmd)
demultiplex_cmd_group.add_command(select_project_cmd)
demultiplex_cmd_group.add_command(finish_group)
demultiplex_cmd_group.add_command(create_report_cmd)
