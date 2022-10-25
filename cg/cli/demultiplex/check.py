"""Check for newly demultiplex runs."""
import logging
from pathlib import Path
from typing import List

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.cg_config import CGConfig


@click.group(name="check")
def check_group():
    """Check for new demultiplexing."""


@click.command(name="check_new_demultiplex")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def check_new_demultiplex(context: CGConfig, dry_run: bool):
    """Command to check for new demultiplexed flow cells."""
    logging.debug("Checking for new demultiplexed flowcells")

    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_flow_cell_out_dirs: List[
        Path
    ] = demultiplex_api.get_all_demultiplex_flow_cells_out_dirs()
