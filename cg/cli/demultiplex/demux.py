import logging
from pathlib import Path

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import FlowCellError
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)

DRY_RUN = click.option("--dry-run", is_flag=True)


@click.command(name="all")
@OPTION_BCL_CONVERTER
@DRY_RUN
@click.option("--flow-cells-directory", type=click.Path(exists=True, file_okay=False))
@click.pass_obj
def demultiplex_all(
    context: CGConfig, bcl_converter: str, flow_cells_directory: click.Path, dry_run: bool
):
    """Demultiplex all flow cells that are ready under the flow cells directory."""
    LOG.info(f"Running cg demultiplex all, using {bcl_converter}.")
    if flow_cells_directory:
        flow_cells_directory: Path = Path(str(flow_cells_directory))
    else:
        flow_cells_directory: Path = Path(context.demultiplex.run_dir)
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    tb_api: TrailblazerAPI = context.trailblazer_api
    LOG.info(f"Search for flow cells ready to demultiplex in {flow_cells_directory}")
    for sub_dir in flow_cells_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info(f"Found directory {sub_dir}")
        try:
            flow_cell = FlowCellDirectoryData(flow_cell_path=sub_dir, bcl_converter=bcl_converter)
        except FlowCellError:
            continue

        if not demultiplex_api.is_demultiplexing_possible(flow_cell=flow_cell) and not dry_run:
            continue

        if not flow_cell.validate_sample_sheet():
            LOG.warning(
                f"Malformed sample sheet. Run cg demultiplex samplesheet validate {flow_cell.sample_sheet_path}",
            )
            continue

        slurm_job_id: int = demultiplex_api.start_demultiplexing(flow_cell=flow_cell)
        demultiplex_api.add_to_trailblazer(
            tb_api=tb_api, slurm_job_id=slurm_job_id, flow_cell=flow_cell
        )


@click.command(name="flow-cell")
@click.argument("flow-cell-name")
@DRY_RUN
@OPTION_BCL_CONVERTER
@click.pass_obj
def demultiplex_flow_cell(
    context: CGConfig,
    dry_run: bool,
    flow_cell_name: str,
    bcl_converter: str,
):
    """Demultiplex a flow cell.

    flow cell name is the flow cell run directory name, e.g. '201203_A00689_0200_AHVKJCDRXX'
    """

    LOG.info(f"Running cg demultiplex flow cell, using {bcl_converter}")
    flow_cell_directory: Path = Path(context.demultiplex.run_dir, flow_cell_name)

    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    LOG.info(f"setting flow cell id to {flow_cell_name}")
    LOG.info(f"setting out dir to {demultiplex_api.out_dir}")

    try:
        flow_cell = FlowCellDirectoryData(
            flow_cell_path=flow_cell_directory, bcl_converter=bcl_converter
        )
    except FlowCellError as error:
        raise click.Abort from error

    if not demultiplex_api.is_demultiplexing_possible(flow_cell=flow_cell) and not dry_run:
        LOG.warning("Can not start demultiplexing!")
        return

    if not flow_cell.validate_sample_sheet():
        LOG.warning(
            f"Malformed sample sheet. Run cg demultiplex samplesheet validate {flow_cell.sample_sheet_path}"
        )
        raise click.Abort

    slurm_job_id: int = demultiplex_api.start_demultiplexing(flow_cell=flow_cell)
    tb_api: TrailblazerAPI = context.trailblazer_api
    demultiplex_api.add_to_trailblazer(
        tb_api=tb_api, slurm_job_id=slurm_job_id, flow_cell=flow_cell
    )


@click.command(name="delete-flow-cell")
@click.option(
    "-f",
    "--flow-cell-name",
    required=True,
    help="The name of the flow cell you want to delete, e.g. HVKJCDRXX",
)
@click.option(
    "--demultiplexing-dir", is_flag=True, help="Delete flow cell demultiplexed dir on file system"
)
@click.option("--cg-stats", is_flag=True, help="Delete flow cell in cg-stats")
@click.option("--housekeeper", is_flag=True, help="Delete flow cell in housekeeper")
@click.option("--init-files", is_flag=True, help="Delete flow cell init-files")
@click.option("--run-dir", is_flag=True, help="Delete flow cell run on file system")
@click.option(
    "--sample-lane-sequencing-metrics",
    is_flag=True,
    help="Delete flow cell in sample lane sequencing metrics",
)
@click.option(
    "--status-db",
    is_flag=True,
    help="Delete flow cell in status-db, if passed all other entries are also deleted",
)
@click.option("--yes", is_flag=True, help="Pass yes to click confirm")
@DRY_RUN
@click.pass_obj
def delete_flow_cell(
    context: CGConfig,
    dry_run: bool,
    demultiplexing_dir: bool,
    cg_stats: bool,
    housekeeper: bool,
    init_files: bool,
    run_dir: bool,
    sample_lane_sequencing_metrics: bool,
    status_db: bool,
    yes: bool,
    flow_cell_name: str,
):
    """Delete a flow cell. If --status-db is passed then all other options will be treated as True."""

    delete_demux_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=context, dry_run=dry_run, flow_cell_name=flow_cell_name
    )

    if yes or click.confirm(
        f"Are you sure you want to delete the flow cell from the following databases:\n"
        f"cg-stats={True if status_db else cg_stats}\nDemultiplexing-dir={True if status_db else demultiplexing_dir}\n"
        f"Housekeeper={True if status_db else housekeeper}\nInit_files={True if status_db else init_files}\n"
        f"Run-dir={True if status_db else run_dir}\nStatusdb={status_db}"
        f"\nSample-lane-sequencing-metrics={True if sample_lane_sequencing_metrics else sample_lane_sequencing_metrics}\n"
    ):
        delete_demux_api.delete_flow_cell(
            cg_stats=cg_stats,
            demultiplexing_dir=demultiplexing_dir,
            housekeeper=housekeeper,
            init_files=init_files,
            sample_lane_sequencing_metrics=sample_lane_sequencing_metrics,
            run_dir=run_dir,
            status_db=status_db,
        )
