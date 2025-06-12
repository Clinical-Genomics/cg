import datetime as dt
import logging
import shutil
from pathlib import Path

import rich_click as click
from dateutil.parser import parse as parse_date

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.utils import TOWER_WORKFLOW_TO_ANALYSIS_API_MAP
from cg.cli.workflow.utils import validate_force_store_option
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Workflow
from cg.constants.cli_options import COMMENT, DRY_RUN, FORCE, SKIP_CONFIRMATION
from cg.constants.observations import LOQUSDB_SUPPORTED_WORKFLOWS
from cg.exc import IlluminaRunsNeededError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_pon import BalsamicPonAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.store import Store

ARGUMENT_BEFORE_STR = click.argument("before_str", type=str)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)
ARGUMENT_WORKFLOW = click.argument("workflow", required=True)
OPTION_ANALYSIS_PARAMETERS_CONFIG = click.option(
    "--config-artic", type=str, help="Config with computational and lab related settings"
)
OPTION_LOQUSDB_SUPPORTED_WORKFLOW = click.option(
    "--workflow",
    type=click.Choice(LOQUSDB_SUPPORTED_WORKFLOWS),
    help="Limit observations upload to a specific workflow",
)

LOG = logging.getLogger(__name__)


@click.command("ensure-illumina-runs-on-disk")
@ARGUMENT_CASE_ID
@click.pass_obj
def ensure_illumina_runs_on_disk(context: CGConfig, case_id: str):
    """
    Check if Illumina runs are on disk for a given case.
    If not, request Illumina run and raise IlluminaRunsNeededError.
    """
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    status_db: Store = context.status_db
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    if not status_db.are_all_illumina_runs_on_disk(case_id=case_id):
        if analysis_api.status_db.is_case_down_sampled(case_id=case_id):
            LOG.debug("All samples have been down sampled. Flow cell check not applicable")
            return
        elif analysis_api.status_db.is_case_external(case_id=case_id):
            LOG.debug("All samples are external. Flow cell check not applicable")
            return
        raise IlluminaRunsNeededError(
            "Analysis cannot be started: all flow cells need to be on disk to run the analysis"
        )
    LOG.info("All Illumina runs present on disk")


@click.command("resolve-compression")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def resolve_compression(context: CGConfig, case_id: str, dry_run: bool):
    """Handles cases where decompression is needed before starting analysis."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    analysis_api.resolve_decompression(case_id=case_id, dry_run=dry_run)


@click.command("link")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def link(context: CGConfig, case_id: str, dry_run: bool):
    """Link FASTQ files for all samples in a case."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    if dry_run:
        return
    analysis_api.link_fastq_files(case_id=case_id)


@click.command("store")
@ARGUMENT_CASE_ID
@COMMENT
@DRY_RUN
@FORCE
@click.pass_obj
def store(context: CGConfig, case_id: str, comment: str | None, dry_run: bool, force: bool):
    """Store finished analysis files in Housekeeper and StatusDB.
    If the force flag is added, the command will:
      - Store bundles in Housekeeper even if the files are incomplete (skip Hermes validation)
      - Overwrite existing completed_at date in StatusDB if the Analysis is already stored
      - Require that a comment is provided explaining the reason for the force-storing
    """
    validate_force_store_option(force=force, comment=comment)
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    if dry_run:
        LOG.info(f"Dry run: Would have stored deliverables for {case_id}")
        return
    try:
        analysis_api.upload_bundle_housekeeper(case_id=case_id, dry_run=dry_run, force=force)
        analysis_api.update_analysis_as_completed_statusdb(
            case_id=case_id, comment=comment, dry_run=dry_run, force=force
        )
        analysis_api.set_statusdb_action(case_id=case_id, action=None, dry_run=dry_run)
    except Exception as exception_object:
        housekeeper_api.rollback()
        status_db.session.rollback()
        LOG.error(f"Error storing deliverables for case {case_id} - {exception_object}")
        raise


@click.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store bundles for all finished analyses in Housekeeper."""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_store():
        LOG.info(f"Storing deliverables for {case_obj.internal_id}")
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error(f"Error storing {case_obj.internal_id}: {exception_object}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@click.command("rsync-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_obj
def rsync_past_run_dirs(
    context: CGConfig, before_str: str, dry_run: bool, skip_confirmation: bool
) -> None:
    """Remove deliver workflow commands."""

    rsync_api: DeliveryRsyncService = context.delivery_rsync_service

    before: dt.datetime = parse_date(before_str)

    for process in rsync_api.rsync_processes:
        if rsync_api.process_ready_to_clean(before=before, process=process):
            if skip_confirmation or click.confirm(f"Do you want to remove all files in {process}?"):
                if dry_run:
                    LOG.info(f"Would have removed {process}")
                    continue
                LOG.info(f"Removing {process.as_posix()}")
                shutil.rmtree(process, ignore_errors=True)
        else:
            LOG.info(f"{process.as_posix()} is still young")


@click.command("clean-run-dir")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def clean_run_dir(context: CGConfig, skip_confirmation: bool, case_id: str, dry_run: bool = False):
    """Remove workflow run directory."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.check_analysis_ongoing(case_id=case_id)

    analysis_path: list[Path] | Path = analysis_api.get_case_path(case_id)

    if dry_run:
        LOG.info(f"Would have deleted: {analysis_path}")
        return EXIT_SUCCESS

    analysis_api.clean_run_dir(
        case_id=case_id, skip_confirmation=skip_confirmation, case_path=analysis_path
    )


@click.command("past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of old case run dirs."""

    exit_code = EXIT_SUCCESS
    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    before = parse_date(before_str)
    possible_cleanups = analysis_api.get_analyses_to_clean(before=before)
    LOG.info(f"Cleaning {len(possible_cleanups)} analyses created before {before}")

    for analysis in possible_cleanups:
        case_id = analysis.case.internal_id
        try:
            LOG.info(f"Cleaning {analysis_api.workflow} output for {case_id}")
            context.invoke(
                clean_run_dir, skip_confirmation=skip_confirmation, case_id=case_id, dry_run=dry_run
            )
        except FileNotFoundError:
            continue
        except Exception as error:
            LOG.error(f"Failed to clean directories for case {case_id} - {repr(error)}")
            exit_code = EXIT_FAIL

    if exit_code:
        raise click.Abort
    LOG.info(f"Done cleaning {analysis_api.workflow} output")


@click.command("balsamic-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("balsamic-umi-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_umi_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic umi case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicUmiAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("balsamic-pon-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_pon_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic pon case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicPonAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("fluffy-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def fluffy_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" Fluffy case run dirs."""

    context.obj.meta_apis["analysis_api"] = FluffyAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("mip-dna-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def mip_dna_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" MIP_DNA case run dirs."""

    context.obj.meta_apis["analysis_api"] = MipDNAAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("mip-rna-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def mip_rna_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" MIP_RNA case run dirs."""

    context.obj.meta_apis["analysis_api"] = MipRNAAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("mutant-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def mutant_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" MUTANT case run dirs."""

    context.obj.meta_apis["analysis_api"] = MutantAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("rnafusion-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def rnafusion_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" RNAFUSION case run dirs."""

    context.obj.meta_apis["analysis_api"] = RnafusionAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("microsalt-past-run-dirs")
@SKIP_CONFIRMATION
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def microsalt_past_run_dirs(
    context: click.Context, before_str: str, skip_confirmation: bool = False, dry_run: bool = False
):
    """Clean up of "old" microSALT case run dirs."""

    context.obj.meta_apis["analysis_api"]: MicrosaltAnalysisAPI = MicrosaltAnalysisAPI(context.obj)
    context.invoke(
        past_run_dirs, skip_confirmation=skip_confirmation, dry_run=dry_run, before_str=before_str
    )


@click.command("tower-past-run-dirs")
@SKIP_CONFIRMATION
@ARGUMENT_WORKFLOW
@ARGUMENT_BEFORE_STR
@click.pass_context
def tower_past_run_dirs(
    context: click.Context, before_str: str, workflow: Workflow, skip_confirmation: bool = False
):
    """Clean up of "old" tower case run dirs."""
    if workflow not in TOWER_WORKFLOW_TO_ANALYSIS_API_MAP:
        LOG.error(f"Please ensure that the provided workflow {workflow} is using Tower")
        raise click.Abort()
    analysis_api: NfAnalysisAPI = TOWER_WORKFLOW_TO_ANALYSIS_API_MAP.get(workflow)(context.obj)
    analysis_api.clean_past_run_dirs(before_date=before_str, skip_confirmation=skip_confirmation)
