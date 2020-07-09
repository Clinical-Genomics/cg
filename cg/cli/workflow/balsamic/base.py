""" Add CLI support to create config and/or start BALSAMIC """
import logging
import shutil
import click

from pathlib import Path
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI

LOG = logging.getLogger(__name__)

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_DRY = click.option(
    "-d", "--dry-run", "dry", help="Print command to console without executing"
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


@click.group(invoke_without_command=True)
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_PANEL_BED
@OPTION_ANALYSIS_TYPE
@OPTION_RUN_ANALYSIS
@OPTION_PRIORITY
@click.pass_context
def balsamic(context, case_id, priority, panel_bed, analysis_type, run_analysis, dry):
    """Cancer workflow """
    context.obj["BalsamicAnalysisAPI"] = BalsamicAnalysisAPI(context.obj)
    if context.invoked_subcommand is None:
        if case_id is None:
            LOG.error("Provide a case!")
            raise click.Abort()

        context.invoke(link, case_id=case_id)
        context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry=dry)
        context.invoke(
            run,
            case_id=case_id,
            priority=priority,
            analysis_type=analysis_type,
            run_analysis=run_analysis,
            dry=dry,
        )


@balsamic.command()
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

    context.obj["BalsamicAnalysisAPI"].link_samples(case_object.links)


@balsamic.command("config-case")
@ARGUMENT_CASE_ID
@OPTION_PANEL_BED
@OPTION_DRY
@click.pass_context
def config_case(context, panel_bed, case_id, dry):
    """Create config file for BALSAMIC analysis for a case"""

    LOG.info(f"Creating config file for {case_id}")

    case_object = context.obj["BalsamicAnalysisAPI"].get_case_object(case_id)

    if not case_object and case_object.links:
        LOG.warning(f"{case_id} invalid!")
        raise click.Abort()

    setup_data = context.obj["BalsamicAnalysisAPI"].get_case_config_params(case_object)

    if len(setup_data) == 0:
        LOG.warning(f"{case_id} has no samples tagged for BALSAMIC analysis!")
        raise click.Abort()

    try:
        arguments = context.obj["BalsamicAnalysisAPI"].get_verified_case_config_params(
            case_id=case_id, panel_bed=panel_bed, setup_data=setup_data,
        )
    except ValueError as e:
        LOG.warning(f"warning text : {e}")
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
    arguments = {
        "priority": priority or context.obj["BalsamicAnalysisAPI"].get_priority(case_id),
        "analysis_type": analysis_type,
        "run_analysis": run_analysis,
        "case_id": case_id,
    }

    context.obj["BalsamicAnalysisAPI"].balsamic_api.run_analysis(
        arguments=arguments, run_analysis=run_analysis, dry=dry
    )


@balsamic.command()
@ARGUMENT_CASE_ID
@click.pass_context
def remove_fastq(context, case_id):
    """Remove stored FASTQ files"""
    work_dir = Path(context.obj["BalsamicAnalysisAPI"].balsamic_api.root_dir / case_id / "fastq")
    if work_dir.exists():
        shutil.rmtree(work_dir)
        LOG.info(f"Path {work_dir} removed successfully")
    else:
        LOG.info(f"Path {work_dir} does not exist")
