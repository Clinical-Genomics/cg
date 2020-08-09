""" Add CLI support to create config and/or start BALSAMIC """
import logging
import shutil
import click
from time import sleep

from pathlib import Path

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.store import Store

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.exc import LimsDataError, BalsamicStartError, BundleAlreadyAddedError
from cg.cli.workflow.balsamic.deliver import deliver as deliver_cmd

LOG = logging.getLogger(__name__)

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing", is_flag=True,
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    required=False,
    help="Panel BED is determined based on capture kit \
    used for library prep. Set this option to override the default",
)
OPTION_ANALYSIS_TYPE = click.option(
    "-a", "--analysis-type", type=click.Choice(["qc", "paired", "single"])
)
OPTION_RUN_ANALYSIS = click.option(
    "-r", "--run-analysis", is_flag=True, default=False, help="Execute in non-dry mode"
)
OPTION_PRIORITY = click.option("-p", "--priority", type=click.Choice(["low", "normal", "high"]))
OPTION_CUSTOMER_ID = click.option("--customer-id")


@click.group(invoke_without_command=True)
@OPTION_DRY
@OPTION_PANEL_BED
@OPTION_ANALYSIS_TYPE
@OPTION_RUN_ANALYSIS
@OPTION_PRIORITY
@click.pass_context
def balsamic(context, priority, panel_bed, analysis_type, run_analysis, dry):
    """Cancer analysis workflow """
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        raise click.Abort()
    config = context.obj
    context.obj["BalsamicAnalysisAPI"] = BalsamicAnalysisAPI(
        balsamic_api=BalsamicAPI(config),
        store=Store(config["database"]),
        housekeeper_api=HousekeeperAPI(config),
        fastq_handler=FastqHandler(config),
        lims_api=LimsAPI(config),
        fastq_api=FastqAPI,
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
        arguments = balsamic_analysis_api.get_verified_config_case_arguments(
            case_id=case_id, panel_bed=panel_bed
        )
        LOG.info(f"Creating config file for {case_id}.")
        balsamic_analysis_api.balsamic_api.config_case(arguments=arguments, dry=dry)
    except (BalsamicStartError, LimsDataError) as e:
        LOG.error(f"Could not create config: {e.message}")
        raise click.Abort()


@balsamic.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_PRIORITY
@OPTION_ANALYSIS_TYPE
@OPTION_RUN_ANALYSIS
@click.pass_context
def run(context, analysis_type, run_analysis, priority, case_id, dry):
    """Run balsamic analysis"""

    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]

    try:
        arguments = {
            "priority": priority or balsamic_analysis_api.get_priority(case_id),
            "analysis_type": analysis_type,
            "run_analysis": run_analysis,
            "sample_config": balsamic_analysis_api.get_config_path(
                case_id=case_id, check_exists=True
            ),
        }
        balsamic_analysis_api.balsamic_api.run_analysis(
            arguments=arguments, run_analysis=run_analysis, dry=dry
        )
    except BalsamicStartError as e:
        LOG.error(f"Could not run analysis: {e.message}")
        raise click.Abort()


@balsamic.command("report-deliver")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_ANALYSIS_TYPE
@click.pass_context
def report_deliver(context, case_id, analysis_type, dry):
    """Create a housekeeper deliverables file for BALSAMIC analysis"""
    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]

    try:
        case_object = balsamic_analysis_api.get_case_object(case_id)
        sample_config = balsamic_analysis_api.get_config_path(
                case_id=case_id, check_exists=True
            )
        analysis_finish = balsamic_analysis_api.get_analysis_finish_path(case_id, check_exists=True)
        LOG.info(f"Found analysis finish file: {analysis_finish}")
        arguments = {
            "sample_config": sample_config,
            "analysis_type": analysis_type,
        }
        balsamic_analysis_api.balsamic_api.report_deliver(arguments=arguments, dry=dry)
    except BalsamicStartError as e:
        LOG.error(f"Could not create report file: {e.message}")
        raise click.Abort()


@balsamic.command("update-housekeeper")
@ARGUMENT_CASE_ID
@click.pass_context
def update_housekeeper(context, case_id):
    """Store a finished analysis in Housekeeper and StatusDB."""

    balsamic_analysis_api = context.obj["BalsamicAnalysisAPI"]
    try:
        balsamic_analysis_api.upload_bundle_housekeeper(case_id=case_id)
        balsamic_analysis_api.upload_analysis_statusdb(case_id=case_id)
    except (BalsamicStartError, BundleAlreadyAddedError) as e:
        LOG.error(f"Could not store bundle in Housekeeper and StatusDB: {e.message}!")
        balsamic_analysis_api.housekeeper_api.rollback()
        balsamic_analysis_api.store.rollback()
        raise click.Abort()


@balsamic.command("start")
@ARGUMENT_CASE_ID
@OPTION_ANALYSIS_TYPE
@OPTION_PRIORITY
@OPTION_RUN_ANALYSIS
@OPTION_DRY
def start(context, case_id, analysis_type, priority, run_analysis, dry):
    """Start full workflow for CASE ID"""
    context.invoke(link, case_id=case_id)
    context.invoke(config_case, case_id=case_id, dry=dry)
    context.invoke(
        run,
        case_id=case_id,
        analysis_type=analysis_type,
        priority=priority,
        run_analysis=run_analysis,
        dry=dry,
    )


@balsamic.command("start-available")
@OPTION_DRY
def start_available(context, dry):
    """Start full workflow for all available cases"""
    for case_object in context.obj["BalsamicAnalysisAPI"].store.cases_to_balsamic_analyze():
        case_id = case_object.internal_id
        LOG.info(f"Starting analysis for {case_id}")
        try:
            context.invoke(start, case_id=case_id, dry=dry, run_analysis="--run-analysis")
        except click.Abort:
            continue


@balsamic.command("deliver-available")
@OPTION_DRY
def deliver_available(context, dry):
    """Deliver bundle data for all available cases"""
    for case_object in context.obj["BalsamicAnalysisAPI"].store.analyses_to_deliver():
        case_id = case_object.internal_id
        LOG.info(f"Storing analysis for {case_id}")
        try:
            context.invoke(report_deliver, case_id=case_id, dry=dry)
            context.invoke(update_housekeeper, case_id=case_id)
        except click.Abort:
            continue


balsamic.add_command(deliver_cmd)
