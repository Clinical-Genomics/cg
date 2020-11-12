"""CLI support to create config and/or start BALSAMIC """

import logging

import click

from cg.apps.environ import environ_email
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.exc import BalsamicStartError, BundleAlreadyAddedError, LimsDataError
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.store import Store
from cg.constants import EXIT_SUCCESS, EXIT_FAIL, Pipeline

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
def balsamic(context):
    """Cancer analysis workflow """
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    config = context.obj
    context.obj["BalsamicAnalysisAPI"] = BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(config),
        store=Store(config["database"]),
        housekeeper_api=HousekeeperAPI(config),
        fastq_handler=FastqHandler(config),
        lims_api=LimsAPI(config),
        trailblazer_api=TrailblazerAPI(config),
    )


@balsamic.command("link")
@ARGUMENT_CASE_ID
@click.pass_context
def link(context, case_id):
    """
    Locates FASTQ files for given CASE_ID.
    The files are renamed, concatenated, and saved in BALSAMIC working directory
    """
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    try:
        LOG.info(f"Linking samples in case {case_id}")
        balsamic_analysis_api.link_samples(case_id)
    except BalsamicStartError as e:
        LOG.error(f"Could not link samples: {e.message}")
        raise click.Abort()


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_PANEL_BED
@OPTION_DRY
@click.pass_context
def config_case(context, panel_bed, case_id, dry):
    """Create config file for BALSAMIC analysis for a given CASE_ID"""
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]

    try:
        LOG.info(f"Creating config file for {case_id}.")
        arguments = balsamic_analysis_api.get_verified_config_case_arguments(
            case_id=case_id,
            panel_bed=panel_bed,
        )
        balsamic_analysis_api.balsamic_api.config_case(arguments=arguments, dry=dry)
    except (BalsamicStartError, LimsDataError) as e:
        LOG.error(f"Could not create config: {e.message}")
        raise click.Abort()


@balsamic.command("run")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_PRIORITY
@OPTION_ANALYSIS_TYPE
@OPTION_RUN_ANALYSIS
@click.pass_context
def run(context, analysis_type, run_analysis, priority, case_id, dry):
    """Run balsamic analysis for given CASE ID"""
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    try:
        LOG.info(f"Running analysis for {case_id}")
        if balsamic_analysis_api.trailblazer_api.is_latest_analysis_ongoing(case_id=case_id):
            LOG.warning(f"{case_id} : analysis is still ongoing - skipping")
            return

        arguments = {
            "priority": priority or balsamic_analysis_api.get_priority(case_id),
            "analysis_type": analysis_type,
            "run_analysis": run_analysis,
            "sample_config": balsamic_analysis_api.get_config_path(
                case_id=case_id, check_exists=True
            ),
            "disable_variant_caller": "mutect"
            if balsamic_analysis_api.get_case_application_type(case_id=case_id) == "wes"
            else None,  # Tell Balsamic to disable mutect for WES analyses.
        }
        balsamic_analysis_api.balsamic_api.run_analysis(
            arguments=arguments, run_analysis=run_analysis, dry=dry
        )
        balsamic_analysis_api.trailblazer_api.mark_analyses_deleted(case_id=case_id)
        balsamic_analysis_api.trailblazer_api.add_pending_analysis(
            case_id=case_id,
            email=environ_email(),
            type=balsamic_analysis_api.get_case_application_type(case_id=case_id),
            out_dir=balsamic_analysis_api.get_case_path(case_id),
            config_path=balsamic_analysis_api.get_slurm_job_ids_path(case_id).as_posix(),
            priority=balsamic_analysis_api.get_priority(case_id),
            data_analysis=Pipeline.BALSAMIC,
        )
        balsamic_analysis_api.set_statusdb_action(case_id=case_id, action="running")
    except BalsamicStartError as e:
        LOG.error(f"Could not run analysis: {e.message}")
        raise click.Abort()


@balsamic.command("report-deliver")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_ANALYSIS_TYPE
@click.pass_context
def report_deliver(context, case_id, analysis_type, dry):
    """Create a housekeeper deliverables file for given CASE ID"""
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    try:
        LOG.info(f"Creating delivery report for {case_id}")
        case_object = balsamic_analysis_api.get_case_object(case_id)
        sample_config = balsamic_analysis_api.get_config_path(case_id=case_id, check_exists=True)
        analysis_finish = balsamic_analysis_api.get_analysis_finish_path(case_id, check_exists=True)
        LOG.info(f"Found analysis finish file: {analysis_finish}")
        arguments = {"sample_config": sample_config, "analysis_type": analysis_type}
        balsamic_analysis_api.balsamic_api.report_deliver(arguments=arguments, dry=dry)
    except BalsamicStartError as e:
        LOG.error(f"Could not create report file: {e.message}")
        raise click.Abort()


@balsamic.command("store-housekeeper")
@ARGUMENT_CASE_ID
@click.pass_context
def store_housekeeper(context, case_id):
    """Store a finished analysis in Housekeeper and StatusDB."""
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    try:
        LOG.info(f"Storing bundle data in Housekeeper for {case_id}")
        balsamic_analysis_api.upload_bundle_housekeeper(case_id=case_id)
        LOG.info(f"Storing Analysis in ClinicalDB for {case_id}")
        balsamic_analysis_api.upload_analysis_statusdb(case_id=case_id)
    except (BundleAlreadyAddedError, FileExistsError) as e:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {e.message}!")
        balsamic_analysis_api.housekeeper_api.rollback()
        balsamic_analysis_api.store.rollback()
        raise click.Abort()
    except BalsamicStartError as e:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {e.message}!")
        raise click.Abort()


@balsamic.command("start")
@ARGUMENT_CASE_ID
@OPTION_ANALYSIS_TYPE
@OPTION_PRIORITY
@OPTION_DRY
@OPTION_PANEL_BED
@click.pass_context
def start(context, case_id, analysis_type, panel_bed, priority, dry):
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
def store(context, case_id, analysis_type, dry):
    """Generate Housekeeper report for CASE ID and store in Housekeeper"""
    LOG.info(f"Storing analysis for {case_id}")
    context.invoke(report_deliver, case_id=case_id, analysis_type=analysis_type, dry=dry)
    context.invoke(store_housekeeper, case_id=case_id)


@balsamic.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context, dry):
    """Start full workflow for all available BALSAMIC cases"""
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    exit_code = EXIT_SUCCESS
    for case_id in balsamic_analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_id, dry=dry)
        except click.Abort:
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error(f"Unspecified error occurred - {e.__class__.__name__}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()


@balsamic.command("store-available")
@OPTION_DRY
@click.pass_context
def store_available(context, dry):
    """Store bundle data for all available Balsamic cases"""
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    exit_code = EXIT_SUCCESS
    for case_id in balsamic_analysis_api.get_cases_to_store():
        try:
            context.invoke(store, case_id=case_id, dry=dry)
        except click.Abort:
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error(f"Unspecified error occurred - {e.__class__.__name__}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort()
