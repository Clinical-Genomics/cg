from typing import List, Union

import click
import datetime as dt
import logging
import shutil

from pathlib import Path

from cgmodels.cg.constants import Pipeline

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.observations import LOQUSDB_SUPPORTED_PIPELINES
from cg.exc import FlowcellsNeededError, DecompressionNeededError
from cg.meta.rsync import RsyncAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from dateutil.parser import parse as parse_date

OPTION_DRY = click.option(
    "-d", "--dry-run", help="Simulate process without executing", is_flag=True
)
OPTION_YES = click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
ARGUMENT_BEFORE_STR = click.argument("before_str", type=str)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_ANALYSIS_PARAMETERS_CONFIG = click.option(
    "--config-artic", type=str, help="Config with computational and lab related settings"
)
OPTION_LOQUSDB_SUPPORTED_PIPELINES = click.option(
    "--pipeline",
    type=click.Choice(LOQUSDB_SUPPORTED_PIPELINES),
    help="Limit observations upload to a specific pipeline",
)

LOG = logging.getLogger(__name__)


@click.command("ensure-flowcells-ondisk")
@ARGUMENT_CASE_ID
@click.pass_obj
def ensure_flowcells_ondisk(context: CGConfig, case_id: str):
    """Check if flowcells are on disk for given case. If not, request flowcells and raise FlowcellsNeededError."""
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
    """Handles cases where decompression is needed before starting analysis."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    is_decompression_running: bool = analysis_api.resolve_decompression(
        case_id=case_id, dry_run=dry_run
    )
    if is_decompression_running:
        raise DecompressionNeededError("Workflow interrupted: decompression is not finished")


@click.command("link")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def link(context: CGConfig, case_id: str, dry_run: bool):
    """Link FASTQ files for all samples in a case."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)
    if dry_run:
        return
    analysis_api.link_fastq_files(case_id=case_id)


@click.command("store")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def store(context: CGConfig, case_id: str, dry_run: bool):
    """Store finished analysis files in Housekeeper."""

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
    """Store bundles for all finished analyses in Housekeeper."""

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


@click.command("rsync-past-run-dirs")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_BEFORE_STR
@click.pass_obj
def rsync_past_run_dirs(context: CGConfig, before_str: str, dry_run: bool, yes: bool) -> None:
    """Remove deliver workflow commands."""

    rsync_api: RsyncAPI = RsyncAPI(config=context)

    before: dt.datetime = parse_date(before_str)

    for process in rsync_api.rsync_processes:
        if rsync_api.process_ready_to_clean(before=before, process=process):
            if yes or click.confirm(f"Do you want to remove all files in {process}?"):
                if dry_run:
                    LOG.info(f"Would have removed {process}")
                    continue
                LOG.info(f"Removing {process.as_posix()}")
                shutil.rmtree(process, ignore_errors=True)
        else:
            LOG.info(f"{process.as_posix()} is still young")


@click.command("clean-run-dir")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_obj
def clean_run_dir(context: CGConfig, yes: bool, case_id: str, dry_run: bool = False):
    """Remove workflow run directory."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.verify_case_id_in_statusdb(case_id)
    analysis_api.check_analysis_ongoing(case_id=case_id)

    analysis_path: Union[List[Path], Path] = analysis_api.get_case_path(case_id)

    if dry_run:
        LOG.info(f"Would have deleted: {analysis_path}")
        return EXIT_SUCCESS

    analysis_api.clean_run_dir(case_id=case_id, yes=yes, case_path=analysis_path)


@click.command("past-run-dirs")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_BEFORE_STR
@click.pass_context
def past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of old case run dirs."""

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
        except FileNotFoundError:
            continue
        except Exception as error:
            LOG.error("Failed to clean directories for case %s - %s", case_id, error)
            exit_code = EXIT_FAIL

    if exit_code:
        raise click.Abort
    LOG.info("Done cleaning %s output ", analysis_api.pipeline)


@click.command("balsamic-past-run-dirs")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("fluffy-past-run-dirs")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_BEFORE_STR
@click.pass_context
def fluffy_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Fluffy case run dirs."""

    context.obj.meta_apis["analysis_api"] = FluffyAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("mip-past-run-dirs")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_BEFORE_STR
@click.pass_context
def mip_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MIP case run dirs."""

    context.obj.meta_apis["analysis_api"] = MipDNAAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("mutant-past-run-dirs")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_BEFORE_STR
@click.pass_context
def mutant_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MUTANT case run dirs."""

    context.obj.meta_apis["analysis_api"] = MutantAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("microsalt-past-run-dirs")
@OPTION_YES
@OPTION_DRY
@ARGUMENT_BEFORE_STR
@click.pass_context
def microsalt_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" microSALT case run dirs."""

    context.obj.meta_apis["analysis_api"]: MicrosaltAnalysisAPI = MicrosaltAnalysisAPI(context.obj)

    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)
