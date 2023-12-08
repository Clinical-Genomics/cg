"""Module for demultiplexing CLI."""
import logging

import click

from cg.cli.demultiplex.demux import (
    confirm_flow_cell_sync,
    copy_novaseqx_flow_cells,
    create_manifest_files,
    demultiplex_all,
    demultiplex_flow_cell,
)
from cg.cli.demultiplex.finish import finish_group
from cg.cli.demultiplex.sample_sheet import sample_sheet_commands

LOG = logging.getLogger(__name__)


@click.group(name="demultiplex")
def demultiplex_cmd_group():
    """Command group for the demultiplex CLI."""
    LOG.info("Running cg demultiplex.")


demultiplex_cmd_group: click.Group
for sub_cmd in [
    create_manifest_files,
    confirm_flow_cell_sync,
    demultiplex_flow_cell,
    demultiplex_all,
    finish_group,
    copy_novaseqx_flow_cells,
    sample_sheet_commands,
]:
    demultiplex_cmd_group.add_command(sub_cmd)
