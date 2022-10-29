"""Check for newly demultiplex runs."""
import logging
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import List

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.cli import transfer
from cg.exc import FlowcellError
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell
from cg.utils import Process


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
                if flowcell.is_hiseq_x():
                    logging.info(f"cgstats add --machine X {demultiplex_flow_cell_out_dir}")
                    cgstats_add_parameters = [
                        "add",
                        "--machine",
                        "X",
                        {demultiplex_flow_cell_out_dir},
                    ]
                    cgstats_process: Process = Process(binary="cgstats")
                    cgstats_process.run_command(parameters=cgstats_add_parameters, dry_run=dry_run)
                    for project in Path(
                        demultiplex_flow_cell_out_dirs, "Unaligned", "Project"
                    ).iterdir():
                        stdout_file: Path = Path(
                            demultiplex_flow_cell_out_dirs,
                            "-".join("stats", project_id, flow_cell_run_name),
                            ".txt",
                        )
                        (_, project_id) = project.name.split("_")
                        logging.info(f"cgstats select --project {project_id} {flow_cell_run_name}")
                        cgstats_select_parameters: List[str] = [
                            "selected",
                            "--project",
                            project_id,
                            flow_cell_run_name,
                        ]
                        with open(stdout_file, "w") as file:
                            with redirect_stdout(file):
                                cgstats_process.run_command(
                                    parameters=cgstats_select_parameters, dry_run=dry_run
                                )

                    cgstats_lane_parameters: List[str] = [
                        "lanestats",
                        demultiplex_flow_cell_out_dirs,
                    ]
                    logging.info(f"cgstats lanestats {demultiplex_flow_cell_out_dirs}")
                    cgstats_process.run_command(parameters=cgstats_lane_parameters, dry_run=dry_run)
                today: str = datetime.datetime.strptime(datetime.date, "%Y-%m-%d")
                context.invoke(flowcell, flow_cell_run_name, content=context.forward(transfer))

        else:
            logging.info(f"{flow_cell_run_name} is not yet completely copied")
