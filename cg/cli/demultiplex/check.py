"""Check for newly demultiplex runs."""
import logging
from pathlib import Path
from typing import List

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.exc import FlowcellError
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell


@click.group(name="check")
def check_group():
    """Check for new demultiplexing."""


@click.command(name="check_new_demultiplex")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def check_new_demultiplex(context: CGConfig, dry_run: bool):
    """Command to check for new demultiplexed flow cells prior to Novaseq."""
    logging.debug("Checking for new demultiplexed flowcells")

    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_flow_cell_out_dirs: List[
        Path
    ] = demultiplex_api.get_all_demultiplex_flow_cells_out_dirs()
    for demultiplex_flow_cell_out_dir in demultiplex_flow_cell_out_dirs:
        flow_cell_run_name: str = demultiplex_flow_cell_out_dir.name
        try:
            flowcell: Flowcell = Flowcell(flowcell_path=demultiplex_flow_cell_out_dir)
        except FlowcellError:
            continue
        if flowcell.is_prior_novaseq_copy_completed():
            if flowcell.is_prior_novaseq_delivery_started():
                logging.info(
                    f"{flow_cell_run_name} copy is complete and delivery has already started"
                )
            else:
                logging.info(f"{flow_cell_run_name} copy is complete and delivery will start")
                Path(demultiplex_flow_cell_out_dir, "delivery.txt").touch()
        else:
            logging.info(f"{flow_cell_run_name} is not yet completely copied")
