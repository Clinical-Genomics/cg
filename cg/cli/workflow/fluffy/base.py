import logging
import click

from cg.apps.hk import HousekeeperAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.NIPTool import NIPToolAPI
from cg.store import Store
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.apps.environ import environ_email
from cg.meta.workflow.fluffy import FluffyAnalysisAPI

OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def fluffy(context):
    """Fluffy workflow"""
    if context.invoked_subcommand is None:
        LOG.info(context.get_help())
        return None
    config = context.obj
    context.obj["fluffy_analysis_api"] = FluffyAnalysisAPI(
        housekeeper_api=HousekeeperAPI(config),
        trailblazer_api=TrailblazerAPI(config),
        niptool_api=NIPToolAPI(config),
        status_db=Store(config["database"]),
        binary=config["Fluffy"]["binary_path"],
        root_dir=config["Fluffy"]["root_dir"],
    )


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def link(context, case_id, dry_run):
    """
    Link fastq and samplesheet files from Housekeeper to analysis folder

    """
    fluffy_analysis_api = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.link_samplesheet(case_id=case_id, dry_run=dry_run)
    fluffy_analysis_api.link_fastq(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def run(context, case_id, dry_run):
    """Run fluffy analysis"""
    fluffy_analysis_api = context.obj["fluffy_analysis_api"]
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
def start(context, case_id, dry_run):
    """Run link and run commands"""
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(run, case_id=case_id, dry_run=dry_run)


@fluffy.command()
@OPTION_DRY
@click.pass_context
def start_available(context, dry_run):
    """Run link and start commands for all cases/batches ready to be analyzed"""
    exit_code = EXIT_SUCCESS
    fluffy_analysis_api = context.obj["fluffy_analysis_api"]
    cases_to_analyze = fluffy_analysis_api.status_db.cases_to_analyze(pipeline="fluffy")
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
@OPTION_DRY
@click.pass_context
def store(context, case_id, dry_run):
    fluffy_analysis_api = context.obj["fluffy_analysis_api"]
    fluffy_analysis_api.upload_bundle_housekeeper(case_id=case_id)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def upload_niptool(context, case_id, dry_run):
    """Upload analysis to NIPT viewer"""
    pass
