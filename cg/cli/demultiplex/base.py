"""Module for demultiplexing CLI."""

import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.demultiplex.demux import (
    confirm_sequencing_run_sync,
    copy_novaseqx_sequencing_runs,
    create_manifest_files,
    demultiplex_all,
    demultiplex_sequencing_run,
)
from cg.cli.demultiplex.finish import finish_group
from cg.cli.demultiplex.sample_sheet import sample_sheet_commands

LOG = logging.getLogger(__name__)


@click.group(name="demultiplex", context_settings=CLICK_CONTEXT_SETTINGS)
def demultiplex_cmd_group():
    """Command group for the demultiplex CLI."""
    LOG.info("Running cg demultiplex.")


demultiplex_cmd_group: click.Group
for sub_cmd in [
    create_manifest_files,
    confirm_sequencing_run_sync,
    demultiplex_sequencing_run,
    demultiplex_all,
    finish_group,
    copy_novaseqx_sequencing_runs,
    sample_sheet_commands,
]:
    demultiplex_cmd_group.add_command(sub_cmd)
