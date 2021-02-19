"""CLI support to create config and/or start BALSAMIC """

import logging

import click
from pydantic import ValidationError

from cg.apps.crunchy import CrunchyAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import (
    BalsamicStartError,
    CgError,
)
from cg.meta.compress import CompressAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store import Store
from cg.utils import Process

LOG = logging.getLogger(__name__)

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing", is_flag=True
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    required=False,
    help="Panel BED is determined based on capture kit \
    used for library prep. Set this option to override the default",
)
OPTION_ANALYSIS_TYPE = click.option(
    "-a",
    "--analysis-type",
    type=click.Choice(["qc", "paired", "single"]),
    help="Setting this option to qc ensures only QC analysis is performed",
)
OPTION_RUN_ANALYSIS = click.option(
    "-r",
    "--run-analysis",
    is_flag=True,
    default=False,
    help="Execute BALSAMIC in non-dry mode",
)
OPTION_PRIORITY = click.option(
    "-p",
    "--priority",
    type=click.Choice(["low", "normal", "high"]),
    help="Job priority in SLURM. Will be set automatically according to priority in ClinicalDB, \
         this option can be used to override server setting",
)


@click.group(invoke_without_command=True)
@click.pass_context
def balsamic(context: click.Context):
    """Cancer analysis workflow """
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    config = context.obj
    status_db = Store(config["database"])
    housekeeper_api = HousekeeperAPI(config)
    crunchy_api = CrunchyAPI(config)
    compress_api = CompressAPI(hk_api=housekeeper_api, crunchy_api=crunchy_api)
    lims_api = LimsAPI(config)
    trailblazer_api = TrailblazerAPI(config)
    hermes_api = HermesApi(config)
    scout_api = ScoutAPI(config)
    prepare_fastq_api = PrepareFastqAPI(store=status_db, compress_api=compress_api)
    context.obj["AnalysisAPI"] = BalsamicAnalysisAPI(
        status_db=status_db,
        housekeeper_api=housekeeper_api,
        lims_api=lims_api,
        trailblazer_api=trailblazer_api,
        hermes_api=hermes_api,
        scout_api=scout_api,
        prepare_fastq_api=prepare_fastq_api,
        process=Process(config["balsamic"]["binary_path"]),
        config=config,
    )


@balsamic.command("link")
@ARGUMENT_CASE_ID
@click.pass_context
def link(context: click.Context, case_id: str):
    """
    Locates FASTQ files for given CASE_ID.
    The files are renamed, concatenated, and saved in BALSAMIC working directory
    """
    analysis_api: BalsamicAnalysisAPI = context.obj["AnalysisAPI"]
    try:
        LOG.info(f"Linking samples in case {case_id}")
        analysis_api.link_samples(case_id)
    except Exception as error:
        LOG.error(f"Could not link samples: {error}")
        raise click.Abort()


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_PANEL_BED
@OPTION_DRY
@click.pass_context
def config_case(context: click.Context, panel_bed: str, case_id: str, dry: bool):
    """Create config file for BALSAMIC analysis for a given CASE_ID"""
    analysis_api: BalsamicAnalysisAPI = context.obj["AnalysisAPI"]
    try:
        LOG.info(f"Creating config file for {case_id}.")
        analysis_api.config_case(case_id=case_id, panel_bed=panel_bed, dry=dry)
    except Exception as error:
        LOG.error(f"Could not create config: {error}")
        raise click.Abort()


@balsamic.command("run")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_PRIORITY
@OPTION_ANALYSIS_TYPE
@OPTION_RUN_ANALYSIS
@click.pass_context
def run(
    context: click.Context,
    analysis_type: str,
    run_analysis: bool,
    priority: str,
    case_id: str,
    dry: bool,
):
    """Run balsamic analysis for given CASE ID"""
    analysis_api: BalsamicAnalysisAPI = context.obj["AnalysisAPI"]
    try:
        LOG.info(f"Running analysis for {case_id}")
        if analysis_api.trailblazer_api.is_latest_analysis_ongoing(case_id=case_id):
            LOG.warning(f"{case_id} : analysis is still ongoing - skipping")
            return

        analysis_api.run_analysis(
            case_id=case_id,
            analysis_type=analysis_type,
            run_analysis=run_analysis,
            priority=priority,
            dry=dry,
        )
        if dry:
            return
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
    except CgError as e:
        LOG.error(f"Could not run analysis: {e.message}")
        raise click.Abort()


@balsamic.command("report-deliver")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_ANALYSIS_TYPE
@click.pass_context
def report_deliver(context: click.Context, case_id: str, analysis_type: str, dry: bool):
    """Create a housekeeper deliverables file for given CASE ID"""
    analysis_api: BalsamicAnalysisAPI = context.obj["AnalysisAPI"]
    try:
        analysis_api.report_deliver(case_id=case_id, analysis_type=analysis_type, dry=dry)
    except BalsamicStartError as e:
        LOG.error(f"Could not create report file: {e.message}")
        raise click.Abort()


@balsamic.command("store-housekeeper")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def store_housekeeper(context: click.Context, case_id: str):
    """Store a finished analysis in Housekeeper and StatusDB."""
    analysis_api: BalsamicAnalysisAPI = context.obj["AnalysisAPI"]
    try:
        analysis_api.upload_bundle_housekeeper(case_id=case_id)
        analysis_api.upload_bundle_statusdb(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
    except ValidationError as error:
        LOG.warning("Deliverables file is malformed")
        LOG.warning(error)
        raise click.Abort
    except Exception as error:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {error}!")
        analysis_api.housekeeper_api.rollback()
        analysis_api.status_db.rollback()
        raise click.Abort()


@balsamic.command("start")
@ARGUMENT_CASE_ID
@OPTION_ANALYSIS_TYPE
@OPTION_PRIORITY
@OPTION_DRY
@OPTION_PANEL_BED
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    analysis_type: str,
    panel_bed: str,
    priority: str,
    dry: bool,
):
    """Start full workflow for CASE ID"""
    LOG.info(f"Starting analysis for {case_id}")
    context.invoke(link, case_id=case_id)
    context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry=dry)
    context.invoke(
        run,
        case_id=case_id,
        analysis_type=analysis_type,
        priority=priority,
        run_analysis="--run-analysis",
        dry=dry,
    )


@balsamic.command("store")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_ANALYSIS_TYPE
@click.pass_context
def store(context: click.Context, case_id: str, analysis_type: str, dry: bool):
    """Generate Housekeeper report for CASE ID and store in Housekeeper"""
    LOG.info(f"Storing analysis for {case_id}")
    context.invoke(report_deliver, case_id=case_id, analysis_type=analysis_type, dry=dry)
    context.invoke(store_housekeeper, case_id=case_id)


@balsamic.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry: bool):
    """Start full workflow for all available BALSAMIC cases"""
    analysis_api: BalsamicAnalysisAPI = context.obj["AnalysisAPI"]
    exit_code = EXIT_SUCCESS
    for case_id in analysis_api.get_valid_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_id, dry=dry)
        except click.Abort:
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(f"Unspecified error occurred - {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()


@balsamic.command("store-available")
@OPTION_DRY
@click.pass_context
def store_available(context: click.Context, dry: bool):
    """Store bundle data for all available Balsamic cases"""
    analysis_api: BalsamicAnalysisAPI = context.obj["AnalysisAPI"]
    exit_code = EXIT_SUCCESS
    for case_id in analysis_api.get_cases_to_store():
        try:
            context.invoke(store, case_id=case_id, dry=dry)
        except click.Abort:
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(f"Unspecified error occurred - {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()
