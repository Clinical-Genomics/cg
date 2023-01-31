"""CLI support to create config and/or start RNAFUSION."""

import logging

import click
from pydantic import ValidationError

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, link, resolve_compression
from cg.cli.workflow.nextflow.options import (
    OPTION_INPUT,
    OPTION_LOG,
    OPTION_OUTDIR,
    OPTION_PROFILE,
    OPTION_STUB,
    OPTION_TOWER,
    OPTION_WORKDIR,
)
from cg.cli.workflow.rnafusion.options import (
    OPTION_ALL,
    OPTION_ARRIBA,
    OPTION_FROM_START,
    OPTION_FUSIONCATCHER,
    OPTION_FUSIONINSPECTOR_FILTER,
    OPTION_PIZZLY,
    OPTION_REFERENCES,
    OPTION_SQUID,
    OPTION_STARFUSION,
    OPTION_STRANDEDNESS,
    OPTION_TRIM,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.constants import DRY_RUN
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def rnafusion(context: click.Context) -> None:
    """nf-core/rnafusion analysis workflow."""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = RnafusionAnalysisAPI(
        config=context.obj,
    )


rnafusion.add_command(resolve_compression)


@rnafusion.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_STRANDEDNESS
@DRY_RUN
@click.pass_obj
def config_case(
    context: CGConfig,
    case_id: str,
    strandedness: str,
    dry_run: bool,
) -> None:
    """Create samplesheet file for RNAFUSION analysis for a given CASE_ID."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]

    LOG.info(f"Creating samplesheet file for {case_id}.")
    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    try:
        analysis_api.config_case(case_id=case_id, strandedness=strandedness, dry_run=dry_run)
    except CgError as error:
        LOG.error(f"Could not create samplesheet: {error}")
        raise click.Abort()


@rnafusion.command("run")
@ARGUMENT_CASE_ID
@OPTION_LOG
@OPTION_WORKDIR
@OPTION_FROM_START
@OPTION_PROFILE
@OPTION_TOWER
@OPTION_STUB
@OPTION_INPUT
@OPTION_OUTDIR
@OPTION_REFERENCES
@OPTION_TRIM
@OPTION_FUSIONINSPECTOR_FILTER
@OPTION_ALL
@OPTION_PIZZLY
@OPTION_SQUID
@OPTION_STARFUSION
@OPTION_FUSIONCATCHER
@OPTION_ARRIBA
@DRY_RUN
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    log: str,
    work_dir: str,
    from_start: bool,
    profile: str,
    with_tower: bool,
    stub: bool,
    input: str,
    outdir: str,
    genomes_base: str,
    trim: bool,
    fusioninspector_filter: bool,
    all: bool,
    pizzly: bool,
    squid: bool,
    starfusion: bool,
    fusioncatcher: bool,
    arriba: bool,
    dry_run: bool,
) -> None:
    """Run rnafusion analysis for given CASE ID."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    resume = False if from_start else True
    try:
        analysis_api.verify_case_id_in_statusdb(case_id)
        analysis_api.verify_case_config_file_exists(case_id=case_id)
        analysis_api.check_analysis_ongoing(case_id)
        LOG.info(f"Running RNAFUSION analysis for {case_id}")
        analysis_api.run_analysis(
            case_id=case_id,
            log=log,
            work_dir=work_dir,
            resume=resume,
            profile=profile,
            with_tower=with_tower,
            stub=stub,
            input=input,
            outdir=outdir,
            genomes_base=genomes_base,
            trim=trim,
            fusioninspector_filter=fusioninspector_filter,
            all=all,
            pizzly=pizzly,
            squid=squid,
            starfusion=starfusion,
            fusioncatcher=fusioncatcher,
            arriba=arriba,
            dry_run=dry_run,
        )
        analysis_api.set_statusdb_action(case_id=case_id, action="running", dry_run=dry_run)
    except (CgError, ValueError) as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort() from error
    except Exception as error:
        LOG.error(f"Could not run analysis: {error}")
        raise click.Abort() from error


@rnafusion.command("start")
@ARGUMENT_CASE_ID
@OPTION_LOG
@OPTION_WORKDIR
@OPTION_PROFILE
@OPTION_TOWER
@OPTION_STUB
@OPTION_INPUT
@OPTION_OUTDIR
@OPTION_REFERENCES
@OPTION_TRIM
@OPTION_FUSIONINSPECTOR_FILTER
@OPTION_ALL
@OPTION_PIZZLY
@OPTION_SQUID
@OPTION_STARFUSION
@OPTION_FUSIONCATCHER
@OPTION_ARRIBA
@DRY_RUN
@click.pass_context
def start(
    context: CGConfig,
    case_id: str,
    log: str,
    work_dir: str,
    profile: str,
    with_tower: bool,
    stub: bool,
    input: str,
    outdir: str,
    genomes_base: str,
    trim: bool,
    fusioninspector_filter: bool,
    all: bool,
    pizzly: bool,
    squid: bool,
    starfusion: bool,
    fusioncatcher: bool,
    arriba: bool,
    dry_run: bool,
) -> None:
    """Start full workflow for CASE ID."""
    LOG.info(f"Starting analysis for {case_id}")

    try:
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
    except DecompressionNeededError as error:
        LOG.error(error)
        raise click.Abort() from error
    context.invoke(config_case, case_id=case_id, dry_run=dry_run)
    context.invoke(
        run,
        case_id=case_id,
        log=log,
        work_dir=work_dir,
        from_start=True,
        profile=profile,
        with_tower=with_tower,
        stub=stub,
        input=input,
        outdir=outdir,
        genomes_base=genomes_base,
        trim=trim,
        fusioninspector_filter=fusioninspector_filter,
        all=all,
        pizzly=pizzly,
        squid=squid,
        starfusion=starfusion,
        fusioncatcher=fusioncatcher,
        arriba=arriba,
        dry_run=dry_run,
    )


@rnafusion.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False) -> None:
    """Start full workflow for all cases ready for analysis."""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run)
        except CgError as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(f"Unspecified error occurred: {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort


@rnafusion.command("report-deliver")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def report_deliver(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Create a housekeeper deliverables file for given CASE ID."""

    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]

    try:
        analysis_api.verify_case_id_in_statusdb(case_id=case_id)
        analysis_api.verify_analysis_finished(case_id=case_id)
        if not dry_run:
            analysis_api.report_deliver(case_id=case_id)
        else:
            LOG.info("Dry-run")
    except CgError as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not create report file: {error}")
        raise click.Abort()


@rnafusion.command("store-housekeeper")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def store_housekeeper(context: CGConfig, case_id: str, dry_run: bool) -> None:
    """Store a finished RNAFUSION analysis in Housekeeper and StatusDB."""
    analysis_api: AnalysisAPI = context.meta_apis["analysis_api"]
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    status_db: Store = context.status_db

    try:
        analysis_api.verify_case_id_in_statusdb(case_id=case_id)
        analysis_api.verify_analysis_finished(case_id=case_id)
        analysis_api.verify_deliverables_file_exists(case_id=case_id)
        analysis_api.upload_bundle_housekeeper(case_id=case_id, dry_run=dry_run)
        analysis_api.upload_bundle_statusdb(case_id=case_id, dry_run=dry_run)
        analysis_api.set_statusdb_action(case_id=case_id, action=None, dry_run=dry_run)
    except ValidationError as error:
        LOG.warning("Deliverables file is malformed")
        raise error
    except CgError as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}")
        raise click.Abort()
    except Exception as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}!")
        housekeeper_api.rollback()
        status_db.rollback()
        raise click.Abort()


@rnafusion.command("store")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_context
def store(context: click.Context, case_id: str, dry_run: bool) -> None:
    """Generate Housekeeper report for CASE ID and store in Housekeeper."""
    LOG.info(f"Storing analysis for {case_id}")
    context.invoke(report_deliver, case_id=case_id, dry_run=dry_run)
    context.invoke(store_housekeeper, case_id=case_id, dry_run=dry_run)


@rnafusion.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Store bundles for all finished RNAFUSION analyses in Housekeeper."""

    analysis_api: AnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_store():
        LOG.info("Storing RNAFUSION deliverables for %s", case_obj.internal_id)
        try:
            context.invoke(store, case_id=case_obj.internal_id, dry_run=dry_run)
        except Exception as error:
            LOG.error(f"Error storing {case_obj.internal_id}: {error}")
            exit_code: int = EXIT_FAIL
    if exit_code:
        raise click.Abort
