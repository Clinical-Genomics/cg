""" Add CLI support to create config and/or start BALSAMIC """
import logging
import shutil
import click

from pathlib import Path

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.balsamic.api import BalsamicAPI
from cg.apps.balsamic.fastq import FastqHandler
from cg.utils.fastq import FastqAPI
from cg.store import Store

from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.exc import LimsDataError, BalsamicStartError
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
def balsamic(context, priority, panel_bed, analysis_type, run_analysis, customer_id, dry):
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
    LOG.info(f"Linking samples in case {case_id}")
    case_object = context.obj["BalsamicAnalysisAPI"].get_case_object(case_id)
    if not case_object and case_object.links:
        LOG.warning(f"{case_id} invalid!")
        raise click.Abort()
    context.obj["BalsamicAnalysisAPI"].link_samples(case_object)


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_PANEL_BED
@OPTION_DRY
@click.pass_context
def config_case(context, panel_bed, case_id, dry):
    """Create config file for BALSAMIC analysis for a case"""

    LOG.info(f"Creating config file for {case_id}.")
    case_object = context.obj["BalsamicAnalysisAPI"].get_case_object(case_id)
    if not case_object or not case_object.links:
        LOG.warning(f"{case_id} not found or number of samples is {len(case_object.links)}!")
        raise click.Abort()
    sample_data = context.obj["BalsamicAnalysisAPI"].get_sample_params(case_object)
    context.obj["BalsamicAnalysisAPI"].report_sample_table(case_id=case_id, sample_data=sample_data)

    try:
        arguments = context.obj["BalsamicAnalysisAPI"].get_verified_config_params(
            case_id=case_id, panel_bed=panel_bed, sample_data=sample_data,
        )
    except (BalsamicStartError, LimsDataError) as e:
        LOG.warning(f"Could not create config: {e.message}")
        raise click.Abort()
    context.obj["BalsamicAnalysisAPI"].balsamic_api.config_case(arguments=arguments, dry=dry)


@balsamic.command()
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_PRIORITY
@OPTION_ANALYSIS_TYPE
@OPTION_RUN_ANALYSIS
@click.pass_context
def run(context, analysis_type, run_analysis, priority, case_id, dry):
    """Run balsamic analysis"""

    case_object = context.obj["BalsamicAnalysisAPI"].get_case_object(case_id)
    if not case_object or not case_object.links:
        LOG.warning(f"{case_id} not found or number of samples is {len(case_object.links)}!")
        raise click.Abort()

    sample_config = context.obj["BalsamicAnalysisAPI"].get_config_path(case_id)
    if not Path(sample_config).exists():
        LOG.warning(f"No config file found for {case_id}!")
        raise click.Abort()

    arguments = {
        "priority": priority or context.obj["BalsamicAnalysisAPI"].get_priority(case_id),
        "analysis_type": analysis_type,
        "run_analysis": run_analysis,
        "sample_config": sample_config,
    }
    context.obj["BalsamicAnalysisAPI"].balsamic_api.run_analysis(
        arguments=arguments, run_analysis=run_analysis, dry=dry
    )


@balsamic.command("report-deliver")
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_ANALYSIS_TYPE
@click.pass_context
def report_deliver(context, case_id, analysis_type, dry):
    """Create a housekeeper deliverables file for BALSAMIC analysis"""
    case_object = context.obj["BalsamicAnalysisAPI"].get_case_object(case_id)
    if not case_object or not case_object.links:
        LOG.warning(f"{case_id} not found or number of samples is {len(case_object.links)}!")
        raise click.Abort()

    sample_config = context.obj["BalsamicAnalysisAPI"].get_config_path(case_id)
    if not Path(sample_config).exists():
        LOG.warning(f"No config file found for {case_id}!")
        raise click.Abort()

    analysis_finish = context.obj["BalsamicAnalysisAPI"].get_analysis_finish_path(case_id)
    if not Path(analysis_finish).exists():
        LOG.warning(f"Analysis incomplete for {case_id}, deliverables file will not be created!")
        raise click.Abort()

    arguments = {"sample_config": sample_config, "analysis_type": analysis_type}
    context.obj["BalsamicAnalysisAPI"].balsamic_api.report_deliver(arguments=arguments, dry=dry)


@balsamic.command("update-housekeeper")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_context
def update_housekeeper(context, case_id, dry):
    """!!!!!WIP!!!!!!
    Store a finished analysis in Housekeeper."""

    case_object = context.obj["BalsamicAnalysisAPI"].get_case_object(case_id)
    if not case_object or not case_object.links:
        LOG.warning(f"{case_id} not found or number of samples is {len(case_object.links)}!")
        raise click.Abort()

    sample_config = context.obj["BalsamicAnalysisAPI"].get_config_path(case_id)
    if not Path(sample_config).exists():
        LOG.warning(f"No config file found for {case_id}!")
        raise click.Abort()

    deliverables_file_path = context.obj["BalsamicAnalysisAPI"].get_deliverables_file_path(case_id)
    if not Path(deliverables_file_path).exists():
        LOG.warning(f"No deliverables file found for {case_id}")
        raise click.Abort()

    try:
        context.obj["BalsamicAnalysisAPI"].update_housekeeper(
            case_object=case_object,
            sample_config=sample_config,
            deliverables_file_path=deliverables_file_path,
        )
        context.obj["BalsamicAnalysisAPI"].update_statusdb(
            case_object=case_object, sample_config=sample_config,
        )
    except Exception:
        LOG.warning("Could not store bundle in Housekeeper and Statusdb!")
        raise click.Abort()


@balsamic.command()
@ARGUMENT_CASE_ID
@click.pass_context
def remove_fastq(context, case_id):
    """Remove stored FASTQ files from working directory"""
    work_dir = Path(context.obj["BalsamicAnalysisAPI"].balsamic_api.root_dir, case_id, "fastq")
    if work_dir.exists():
        shutil.rmtree(work_dir)
        LOG.info(f"Path {work_dir} removed successfully")
    else:
        LOG.info(f"Path {work_dir} does not exist")


balsamic.add_command(deliver_cmd)
