import logging
from pathlib import Path

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import FlowcellError
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)

DRY_RUN = click.option("--dry-run", is_flag=True)


@click.command(name="all")
@OPTION_BCL_CONVERTER
@DRY_RUN
@click.option("--flowcells-directory", type=click.Path(exists=True, file_okay=False))
@click.pass_obj
def demultiplex_all(
    context: CGConfig, bcl_converter: str, flowcells_directory: click.Path, dry_run: bool
):
    """Demultiplex all flowcells that are ready under the flowcells_directory"""
    LOG.info("Running cg demultiplex all, using %s.", bcl_converter)
    if flowcells_directory:
        flowcells_directory: Path = Path(str(flowcells_directory))
    else:
        flowcells_directory: Path = Path(context.demultiplex.run_dir)
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    tb_api: TrailblazerAPI = context.trailblazer_api
    LOG.info("Search for flowcells ready to demultiplex in %s", flowcells_directory)
    for sub_dir in flowcells_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info("Found directory %s", sub_dir)
        try:
            flowcell_obj = Flowcell(flowcell_path=sub_dir, bcl_converter=bcl_converter)
        except FlowcellError:
            continue

        if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
            continue

        if not flowcell_obj.validate_sample_sheet():
            LOG.warning(
                "Malformed sample sheet. Run cg demultiplex samplesheet validate %s",
                flowcell_obj.sample_sheet_path,
            )
            continue

        delete_demux_api: DeleteDemuxAPI = DeleteDemuxAPI(
            config=context,
            demultiplex_base=demultiplex_api.out_dir,
            dry_run=dry_run,
            run_path=(flowcells_directory / sub_dir),
        )

        delete_demux_api.delete_flow_cell(
            cg_stats=False,
            demultiplexing_dir=True,
            run_dir=False,
            housekeeper=True,
            init_files=False,
            status_db=False,
        )

        slurm_job_id: int = demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)
        demultiplex_api.add_to_trailblazer(
            tb_api=tb_api, slurm_job_id=slurm_job_id, flowcell=flowcell_obj
        )


@click.command(name="flowcell")
@click.argument("flowcell-id")
@DRY_RUN
@OPTION_BCL_CONVERTER
@click.pass_obj
def demultiplex_flowcell(
    context: CGConfig,
    dry_run: bool,
    flowcell_id: str,
    bcl_converter: str,
):
    """Demultiplex a flowcell on slurm using CG

    flowcell-id is the flowcell run directory name, e.g. '201203_A00689_0200_AHVKJCDRXX'
    """

    LOG.info("Running cg demultiplex flowcell, using %s.", bcl_converter)
    flowcell_directory: Path = Path(context.demultiplex.run_dir) / flowcell_id

    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    LOG.info(f"SETTING FLOWCELL ID TO {flowcell_id}")
    LOG.info(f"SETTING OUT DIR TO {demultiplex_api.out_dir}")

    try:
        flowcell_obj = Flowcell(flowcell_path=flowcell_directory, bcl_converter=bcl_converter)
    except FlowcellError as error:
        raise click.Abort from error

    delete_demux_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=context,
        demultiplex_base=demultiplex_api.out_dir,
        dry_run=dry_run,
        run_path=flowcell_directory,
    )

    delete_demux_api.delete_flow_cell(
        cg_stats=True,
        demultiplexing_dir=True,
        run_dir=False,
        housekeeper=True,
        init_files=True,
        status_db=False,
    )

    if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
        LOG.warning("Can not start demultiplexing!")
        return

    if not flowcell_obj.validate_sample_sheet():
        LOG.warning(
            "Malformed sample sheet. Run cg demultiplex samplesheet validate %s",
            flowcell_obj.sample_sheet_path,
        )
        raise click.Abort

    slurm_job_id: int = demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)
    tb_api: TrailblazerAPI = context.trailblazer_api
    demultiplex_api.add_to_trailblazer(
        tb_api=tb_api, slurm_job_id=slurm_job_id, flowcell=flowcell_obj
    )


@click.command(name="delete-flow-cell")
@click.option("--cg-stats", is_flag=True, help="Delete flow cell in cg-stats")
@click.option(
    "-d",
    "--demultiplex-base",
    type=click.Path(exists=True),
    required=True,
    help="Is the base of demultiplexing, e.g. '/home/proj/{ENVIRONMENT}/demultiplexed-runs/'",
)
@click.option(
    "--demultiplexing-dir", is_flag=True, help="Delete flow cell demultiplexed dir on file system"
)
@DRY_RUN
@click.option("--housekeeper", is_flag=True, help="Delete flow cell in housekeeper")
@click.option("--init-files", is_flag=True, help="Delete flow cell init-files")
@click.option("--run-dir", is_flag=True, help="Delete flow cell run on file system")
@click.option(
    "-r",
    "--run-directory",
    type=click.Path(exists=False),
    required=True,
    help="Is the path to the flowcell run directory name, e.g. '/home/proj/{ENVIRONMENT}/flowcells/novaseq/runs/201203_A00689_0200_AHVKJCDRXX'",
)
@click.option(
    "--status-db",
    is_flag=True,
    help="Delete flow cell in status-db, if passed all other entries are also deleted",
)
@click.option("--yes", is_flag=True, help="Pass yes to click confirm")
@click.pass_obj
def delete_flow_cell(
    context: CGConfig,
    dry_run: bool,
    demultiplexing_dir: str,
    cg_stats: bool,
    demultiplex_base: bool,
    housekeeper: bool,
    init_files: bool,
    run_dir: bool,
    run_directory: str,
    status_db: bool,
    yes: bool,
):
    """Delete a flowcell. If --status-db is passed then all other options will be treated as True"""
    demultiplex_base: Path = Path(demultiplex_base)
    run_path: Path = Path(run_directory)

    wipe_demux_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=context, demultiplex_base=demultiplex_base, dry_run=dry_run, run_path=run_path
    )

    if yes or click.confirm(
        f"Are you sure you want to delete the flow cell from the following databases:\n"
        f"cg-stats={True if status_db else cg_stats}\nDemultiplexing-dir={True if status_db else demultiplexing_dir}\n"
        f"Housekeeper={True if status_db else housekeeper}\nInit_files={True if status_db else init_files}\n"
        f"Run-dir={True if status_db else run_dir}\nStatusdb={status_db}"
    ):
        wipe_demux_api.delete_flow_cell(
            cg_stats=cg_stats,
            demultiplexing_dir=demultiplexing_dir,
            housekeeper=housekeeper,
            init_files=init_files,
            run_dir=run_dir,
            status_db=status_db,
        )
