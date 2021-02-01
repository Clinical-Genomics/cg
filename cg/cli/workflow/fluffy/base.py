import logging
import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.NIPTool import NIPToolAPI
from cg.store import Store
from cg.constants import EXIT_SUCCESS, EXIT_FAIL, Pipeline
from cg.apps.environ import environ_email
from cg.meta.workflow.fluffy import FluffyAnalysisAPI

OPTION_DRY = click.option(
    "-d", "--dry-run", "dry_run", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def fluffy(context: click.Context):
    """Fluffy workflow"""
    if context.invoked_subcommand is None:
        LOG.info(context.get_help())
        return None
    config = context.obj
    context.obj["fluffy_analysis_api"] = FluffyAnalysisAPI(
        housekeeper_api=HousekeeperAPI(config),
        trailblazer_api=TrailblazerAPI(config),
        lims_api=LimsAPI(config),
        niptool_api=NIPToolAPI(config),
        status_db=Store(config["database"]),
        config=config["fluffy"],
    )


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def link(context: click.Context, case_id: str, dry_run: bool):
    """
    Link fastq files from Housekeeper to analysis folder

    """
    fluffy_analysis_api: FluffyAnalysisAPI = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.link_fastq_files(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def create_samplesheet(context: click.Context, case_id: str, dry_run: bool):
    """
    Write modified samplesheet file to analysis folder

    """
    fluffy_analysis_api: FluffyAnalysisAPI = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.make_samplesheet(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def run(context: click.Context, case_id: str, dry_run: bool):
    """Run fluffy analysis"""
    fluffy_analysis_api: FluffyAnalysisAPI = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.run_fluffy(case_id=case_id, dry_run=dry_run)
    if dry_run:
        return

    # Submit pending analysis to Trailblazer
    fluffy_analysis_api.trailblazer_api.add_pending_analysis(
        case_id=case_id,
        email=environ_email(),
        type="tgs",
        out_dir=fluffy_analysis_api.get_output_path(case_id).as_posix(),
        config_path=fluffy_analysis_api.get_slurm_job_ids_path(case_id).as_posix(),
        priority=fluffy_analysis_api.get_priority(case_id),
        data_analysis="FLUFFY",
    )

    # Update status_db to running
    case_object = fluffy_analysis_api.status_db.family(case_id)
    case_object.action = "running"
    fluffy_analysis_api.status_db.commit()


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def start(context: click.Context, case_id: str, dry_run: bool):
    """Run link and run commands"""
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(create_samplesheet, case_id=case_id, dry_run=dry_run)
    context.invoke(run, case_id=case_id, dry_run=dry_run)


@fluffy.command()
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool):
    """Run link and start commands for all cases/batches ready to be analyzed"""
    exit_code = EXIT_SUCCESS
    fluffy_analysis_api: FluffyAnalysisAPI = context.obj["fluffy_analysis_api"]
    cases_to_analyze = fluffy_analysis_api.status_db.cases_to_analyze(pipeline=Pipeline.FLUFFY)
    for case_id in cases_to_analyze:
        try:
            context.invoke(start, case_id=case_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error(f"Exception occurred - {exception_object.__class__.__name__}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()


@fluffy.command()
@ARGUMENT_CASE_ID
@click.pass_context
def store(context: click.Context, case_id: str):
    fluffy_analysis_api: FluffyAnalysisAPI = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.upload_bundle_housekeeper(case_id=case_id)
    fluffy_analysis_api.upload_bundle_statusdb(case_id=case_id)


@fluffy.command("store-available")
@OPTION_DRY
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store all finished analyses in Housekeeper"""
    fluffy_analysis_api: FluffyAnalysisAPI = context.obj["fluffy_analysis_api"]
    exit_code: int = EXIT_SUCCESS

    for case_obj in fluffy_analysis_api.get_cases_to_store():
        LOG.info("Storing deliverables for %s", case_obj.internal_id)
        if dry_run:
            continue
        try:
            context.invoke(store, case_id=case_obj.internal_id)
        except Exception:
            exit_code = EXIT_FAIL

    if exit_code:
        raise click.Abort


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def upload_niptool(context: click.Context, case_id, dry_run):
    """Upload analysis to NIPT viewer"""
    pass
