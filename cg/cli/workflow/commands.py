import datetime as dt
import logging
import shutil
from pathlib import Path

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import FlowcellsNeededError, DecompressionNeededError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from dateutil.parser import parse as parse_date

OPTION_DRY = click.option(
    "-d", "--dry-run", help="Print command to console without executing", is_flag=True
)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)

LOG = logging.getLogger(__name__)


@click.command("ensure-flowcells-ondisk")
@ARGUMENT_CASE_ID
@click.pass_obj
def ensure_flowcells_ondisk(context: CGConfig, case_id: str):
    """Check if flowcells are on disk for given case. If not, request flowcells and raise FlowcellsNeededError"""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    if not analysis_api.all_flowcells_on_disk(case_id=case_id):
        raise FlowcellsNeededError(
            "Analysis cannot be started: all flowcells need to be on disk to run the analysis"
        )
    LOG.info("All flowcells present on disk")


@click.command("resolve-compression")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def resolve_compression(context: CGConfig, case_id: str, dry_run: bool):
    """Handles cases where decompression is needed before starting analysis"""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    is_decompression_running: bool = analysis_api.resolve_decompression(
        case_id=case_id, dry_run=dry_run
    )
    if is_decompression_running:
        raise DecompressionNeededError("Workflow interrupted: decompression is not finished")


@click.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def link(context: CGConfig, case_id: str, dry_run: bool):
    """Link FASTQ files for all samples in a case"""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)
    if dry_run:
        return
    analysis_api.link_fastq_files(case_id=case_id)


@click.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def store(context: CGConfig, case_id: str, dry_run: bool):
    """Store finished analysis files in Housekeeper"""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)

    if dry_run:
        LOG.info("Dry run: Would have stored deliverables for %s", case_id)
        return
    try:
        analysis_api.upload_bundle_housekeeper(case_id=case_id)
        analysis_api.upload_bundle_statusdb(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
    except Exception as exception_object:
        housekeeper_api.rollback()
        status_db.rollback()
        LOG.error("Error storing deliverables for case %s - %s", case_id, exception_object)
        raise


@click.command("store-available")
@OPTION_DRY
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store bundles for all finished analyses in Housekeeper"""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_store():
        LOG.info("Storing deliverables for %s", case_obj.internal_id)
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error("Error storing %s: %s", case_obj.internal_id, exception_object)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@click.command("clean-run-dir")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@ARGUMENT_CASE_ID
@click.pass_obj
def clean_run_dir(context: CGConfig, yes: bool, case_id: str, dry_run: bool = False):
    """Remove workflow run directory"""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    status_db: Store = context.status_db
    analysis_api.verify_case_id_in_statusdb(case_id)
    analysis_api.verify_case_path_exists(case_id=case_id)
    analysis_api.check_analysis_ongoing(case_id=case_id)
    analysis_path: Path = analysis_api.get_case_path(case_id)

    if dry_run:
        LOG.info(f"Would have deleted: {analysis_path}")
        return EXIT_SUCCESS

    if yes or click.confirm(f"Are you sure you want to remove all files in {analysis_path}?"):
        if analysis_path.is_symlink():
            LOG.warning(
                f"Will not automatically delete symlink: {analysis_path}, delete it manually",
            )
            return EXIT_FAIL

        shutil.rmtree(analysis_path, ignore_errors=True)
        LOG.info("Cleaned %s", analysis_path)
        analyses: list = status_db.family(case_id).analyses
        for analysis_obj in analyses:
            analysis_obj.cleaned_at = analysis_obj.cleaned_at or dt.datetime.now()
            status_db.commit()


@click.command("past-run-dirs")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("before_str")
@click.pass_context
def past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of old case run dirs"""

    exit_code = EXIT_SUCCESS
    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    before = parse_date(before_str)
    possible_cleanups = analysis_api.get_analyses_to_clean(before=before)
    LOG.info(f"Cleaning {len(possible_cleanups)} analyses created before {before}")

    for analysis in possible_cleanups:
        case_id = analysis.family.internal_id
        try:
            LOG.info("Cleaning %s output for %s", analysis_api.pipeline, case_id)
            context.invoke(clean_run_dir, yes=yes, case_id=case_id, dry_run=dry_run)
        except Exception as error:
            LOG.error("Failed to clean directories for case %s - %s", case_id, error)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
    LOG.info("Done cleaning %s output ", analysis_api.pipeline)


@click.command("balsamic-past-run-dirs")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("before_str")
@click.pass_context
def balsamic_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic case run dirs"""

    context.obj.meta_apis["analysis_api"] = BalsamicAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("mip-past-run-dirs")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("before_str")
@click.pass_context
def mip_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MIP case run dirs"""

    context.obj.meta_apis["analysis_api"] = MipDNAAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("mutant-past-run-dirs")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.option("-d", "--dry-run", is_flag=True, help="Shows cases and files that would be cleaned")
@click.argument("before_str")
@click.pass_context
def mutant_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MUTANT case run dirs"""

    context.obj.meta_apis["analysis_api"] = MutantAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)
