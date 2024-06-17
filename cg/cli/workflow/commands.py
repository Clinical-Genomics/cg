import datetime as dt
import logging
import shutil
from pathlib import Path

import click
from dateutil.parser import parse as parse_date

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import DRY_RUN, FORCE
from cg.constants.observations import LOQUSDB_SUPPORTED_WORKFLOWS
from cg.exc import FlowCellsNeededError
from cg.meta.rsync import RsyncAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_pon import BalsamicPonAnalysisAPI
from cg.meta.workflow.balsamic_qc import BalsamicQCAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store

OPTION_YES = click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
ARGUMENT_BEFORE_STR = click.argument("before_str", type=str)
ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_ANALYSIS_PARAMETERS_CONFIG = click.option(
    "--config-artic", type=str, help="Config with computational and lab related settings"
)
OPTION_LOQUSDB_SUPPORTED_WORKFLOW = click.option(
    "--workflow",
    type=click.Choice(LOQUSDB_SUPPORTED_WORKFLOWS),
    help="Limit observations upload to a specific workflow",
)

LOG = logging.getLogger(__name__)


@click.command("ensure-flow-cells-on-disk")
@ARGUMENT_CASE_ID
@click.pass_obj
def ensure_flow_cells_on_disk(context: CGConfig, case_id: str):
    """Check if flow cells are on disk for a given case. If not, request flow cells and raise FlowcellsNeededError."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    status_db: Store = context.status_db
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    if not status_db.are_all_flow_cells_on_disk(case_id=case_id):
        if analysis_api.status_db.is_case_down_sampled(case_id=case_id):
            LOG.debug("All samples have been down sampled. Flow cell check not applicable")
            return
        elif analysis_api.status_db.is_case_external(case_id=case_id):
            LOG.debug("All samples are external. Flow cell check not applicable")
            return
        raise FlowCellsNeededError(
            "Analysis cannot be started: all flow cells need to be on disk to run the analysis"
        )
    LOG.info("All flow cells present on disk")


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
@DRY_RUN
@FORCE
@click.pass_obj
def store(context: CGConfig, case_id: str, dry_run: bool, force: bool):
    """Store finished analysis files in Housekeeper."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)

    if dry_run:
        LOG.info(f"Dry run: Would have stored deliverables for {case_id}")
        return
    try:
        analysis_api.upload_bundle_housekeeper(case_id=case_id, force=force)
        analysis_api.upload_bundle_statusdb(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
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
@OPTION_YES
@DRY_RUN
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
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def clean_run_dir(context: CGConfig, yes: bool, case_id: str, dry_run: bool = False):
    """Remove workflow run directory."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.check_analysis_ongoing(case_id=case_id)

    analysis_path: list[Path] | Path = analysis_api.get_case_path(case_id)

    if dry_run:
        LOG.info(f"Would have deleted: {analysis_path}")
        return EXIT_SUCCESS

    analysis_api.clean_run_dir(case_id=case_id, yes=yes, case_path=analysis_path)


@click.command("past-run-dirs")
@OPTION_YES
@DRY_RUN
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
        case_id = analysis.case.internal_id
        try:
            LOG.info(f"Cleaning {analysis_api.workflow} output for {case_id}")
            context.invoke(clean_run_dir, yes=yes, case_id=case_id, dry_run=dry_run)
        except FileNotFoundError:
            continue
        except Exception as error:
            LOG.error(f"Failed to clean directories for case {case_id} - {repr(error)}")
            exit_code = EXIT_FAIL

    if exit_code:
        raise click.Abort
    LOG.info(f"Done cleaning {analysis_api.workflow} output")


@click.command("balsamic-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("balsamic-qc-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_qc_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic qc case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicQCAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("balsamic-umi-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_umi_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic umi case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicUmiAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("balsamic-pon-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def balsamic_pon_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Balsamic pon case run dirs."""

    context.obj.meta_apis["analysis_api"] = BalsamicPonAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("fluffy-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def fluffy_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" Fluffy case run dirs."""

    context.obj.meta_apis["analysis_api"] = FluffyAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("mip-dna-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def mip_dna_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MIP_DNA case run dirs."""

    context.obj.meta_apis["analysis_api"] = MipDNAAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("mip-rna-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def mip_rna_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MIP_RNA case run dirs."""

    context.obj.meta_apis["analysis_api"] = MipRNAAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("mutant-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def mutant_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" MUTANT case run dirs."""

    context.obj.meta_apis["analysis_api"] = MutantAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("rnafusion-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def rnafusion_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" RNAFUSION case run dirs."""

    context.obj.meta_apis["analysis_api"] = RnafusionAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)


@click.command("microsalt-past-run-dirs")
@OPTION_YES
@DRY_RUN
@ARGUMENT_BEFORE_STR
@click.pass_context
def microsalt_past_run_dirs(
    context: click.Context, before_str: str, yes: bool = False, dry_run: bool = False
):
    """Clean up of "old" microSALT case run dirs."""

    context.obj.meta_apis["analysis_api"]: MicrosaltAnalysisAPI = MicrosaltAnalysisAPI(context.obj)
    context.invoke(past_run_dirs, yes=yes, dry_run=dry_run, before_str=before_str)
