import logging
import click

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
    """
    Fluffy workflow
    """
    if context.invoked_subcommand is None:
        LOG.info(context.get_help())
        return None
    context.obj["analysis_api"] = FluffyAnalysisAPI(
        config=context.obj,
    )


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def link(context: click.Context, case_id: str, dry_run: bool):
    """
    Link fastq files from Housekeeper to analysis folder
    """
    analysis_api: FluffyAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    analysis_api.link_fastq_files(case_id=case_id, dry_run=dry_run)


@fluffy.command("create-samplesheet")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def create_samplesheet(context: click.Context, case_id: str, dry_run: bool):
    """
    Write modified samplesheet file to case folder
    """
    analysis_api: FluffyAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    analysis_api.make_samplesheet(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def run(context: click.Context, case_id: str, dry_run: bool):
    """
    Run Fluffy analysis
    """
    analysis_api: FluffyAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    analysis_api.run_fluffy(case_id=case_id, dry_run=dry_run)
    if dry_run:
        return
    # Submit analysis for tracking in Trailblazer
    try:
        analysis_api.add_pending_trailblazer_analysis(case_id)
        LOG.info("Submitted case %s to Trailblazer!", case_id)
    except Exception as e:
        LOG.warning("Unable to submit job file to Trailblazer, raised error: %s", e)

    analysis_api.set_statusdb_action(case_id=case_id, action="running")


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def start(context: click.Context, case_id: str, dry_run: bool):
    """
    Starts full Fluffy analysis workflow
    """
    LOG.info("Starting full Fluffy workflow for %s", case_id)
    if dry_run:
        LOG.info("Dry run: the executed commands will not produce output!")
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(create_samplesheet, case_id=case_id, dry_run=dry_run)
    context.invoke(run, case_id=case_id, dry_run=dry_run)


@fluffy.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool):
    """
    Start full Fluffy workflow for all cases/batches ready to be analyzed
    """
    exit_code = EXIT_SUCCESS
    analysis_api: FluffyAnalysisAPI = context.obj["analysis_api"]
    for case_obj in analysis_api.status_db.cases_to_analyze(pipeline=Pipeline.FLUFFY):
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error(f"Exception occurred - {exception_object.__class__.__name__}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()


@fluffy.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def store(context: click.Context, case_id: str, dry_run: bool):
    """
    Store finished analysis files in Housekeeper
    """
    analysis_api: FluffyAnalysisAPI = context.obj["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    if dry_run:
        LOG.info("Dry run: Would have stored deliverables for %s", case_id)
        return
    try:
        analysis_api.upload_bundle_housekeeper(case_id=case_id)
        analysis_api.upload_bundle_statusdb(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
    except Exception as error:
        analysis_api.housekeeper_api.rollback()
        analysis_api.status_db.rollback()
        LOG.error("Error storing deliverables for case %s - %s", case_id, error.__class__.__name__)
        raise


@fluffy.command("store-available")
@OPTION_DRY
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """
    Store bundles for all finished analyses in Housekeeper
    """
    analysis_api: FluffyAnalysisAPI = context.obj["analysis_api"]
    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_store():
        LOG.info("Storing deliverables for %s", case_obj.internal_id)
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception:
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
