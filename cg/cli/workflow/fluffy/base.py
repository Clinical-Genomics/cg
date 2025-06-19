import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import link, resolve_compression, store, store_available
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import DRY_RUN
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig

ARGUMENT_CASE_ID = click.argument("case_id", required=True)
OPTION_EXTERNAL_REF = click.option("-e", "--external-ref", is_flag=True)
OPTION_USE_BWA_MEM = click.option("-b", "--use-bwa-mem", is_flag=True)

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def fluffy(context: click.Context):
    """
    Fluffy workflow
    """
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = FluffyAnalysisAPI(config=context.obj)


fluffy.add_command(link)
fluffy.add_command(resolve_compression)
fluffy.add_command(store)
fluffy.add_command(store_available)


@fluffy.command("create-samplesheet")
@ARGUMENT_CASE_ID
@DRY_RUN
@click.pass_obj
def create_samplesheet(context: CGConfig, case_id: str, dry_run: bool):
    """
    Write modified sample sheet file to case folder
    """
    analysis_api: FluffyAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    analysis_api.make_sample_sheet(case_id=case_id, dry_run=dry_run)


@fluffy.command()
@ARGUMENT_CASE_ID
@DRY_RUN
@click.option("-c", "--config", help="Path to fluffy config in .json format")
@OPTION_EXTERNAL_REF
@OPTION_USE_BWA_MEM
@click.pass_obj
def run(
    context: CGConfig,
    case_id: str,
    dry_run: bool,
    config: str,
    external_ref: bool,
    use_bwa_mem: bool,
):
    """
    Run Fluffy analysis
    """
    analysis_api: FluffyAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.status_db.verify_case_exists(case_internal_id=case_id)
    analysis_api.run_fluffy(
        case_id=case_id,
        workflow_config=config,
        dry_run=dry_run,
        external_ref=external_ref,
        use_bwa_mem=use_bwa_mem,
    )
    if dry_run:
        return

    try:
        analysis_api.on_analysis_started(case_id)
        LOG.info(f"Submitted case {case_id} to Trailblazer!")
    except Exception as error:
        LOG.error(f"Error trying to update analysis for case {case_id}: {error}")


@fluffy.command()
@ARGUMENT_CASE_ID
@DRY_RUN
@click.option("-c", "--config", help="Path to fluffy config in .json format")
@OPTION_EXTERNAL_REF
@OPTION_USE_BWA_MEM
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    dry_run: bool,
    external_ref: bool,
    use_bwa_mem: bool,
    config: str = None,
):
    """
    Starts full Fluffy analysis workflow
    """
    LOG.info(f"Starting full Fluffy workflow for {case_id}")
    if dry_run:
        LOG.info("Dry run: the executed commands will not produce output!")
    analysis_api: FluffyAnalysisAPI = context.obj.meta_apis["analysis_api"]
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(create_samplesheet, case_id=case_id, dry_run=dry_run)
    context.invoke(
        run,
        case_id=case_id,
        config=config,
        dry_run=dry_run,
        external_ref=external_ref,
        use_bwa_mem=use_bwa_mem,
    )


@fluffy.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: FluffyAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case.internal_id, dry_run=dry_run)
        except AnalysisNotReadyError as error:
            LOG.error(error)
        except CgError as error:
            LOG.error(error)
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(f"Unspecified error occurred: {error}")
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
