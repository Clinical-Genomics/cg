""" Add CLI support to start MIP rare disease RNA"""

import logging

import click

from cg.cli.workflow.commands import link, resolve_compression
from cg.cli.workflow.mip.base import config_case, run
from cg.cli.workflow.mip.options import (
    ARGUMENT_CASE_ID,
    EMAIL_OPTION,
    OPTION_DRY,
    OPTION_MIP_DRY_RUN,
    OPTION_PANEL_BED,
    PRIORITY_OPTION,
    START_WITH_PROGRAM,
)
from cg.cli.workflow.mip.store import store as store_cmd
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import CgError, DecompressionNeededError, FlowcellsNeededError
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group("mip-rna")
@click.pass_context
def mip_rna(context: click.Context):
    """Rare disease RNA workflow"""

    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return

    context.obj["analysis_api"] = MipRNAAnalysisAPI(config=context.obj)


mip_rna.add_command(config_case)
mip_rna.add_command(link)
mip_rna.add_command(resolve_compression)
mip_rna.add_command(run)
mip_rna.add_command(store_cmd)


@mip_rna.command()
@PRIORITY_OPTION
@EMAIL_OPTION
@START_WITH_PROGRAM
@OPTION_PANEL_BED
@ARGUMENT_CASE_ID
@OPTION_DRY
@OPTION_MIP_DRY_RUN
@click.option(
    "--skip-evaluation",
    is_flag=True,
    help="Skip mip qccollect evaluation",
)
@click.pass_context
def start(
    context: click.Context,
    case_id: str,
    dry_run: bool,
    email: str,
    mip_dry_run: bool,
    priority: str,
    skip_evaluation: bool,
    start_with: str,
    panel_bed: str,
):
    """Start full MIP-RNA analysis workflow for a case"""

    analysis_api: MipRNAAnalysisAPI = context.obj["analysis_api"]

    analysis_api.verify_case_id_in_statusdb(case_id=case_id)
    LOG.info("Starting full MIP-RNA analysis workflow for case %s", case_id)
    try:
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
        context.invoke(link, case_id=case_id)
        context.invoke(config_case, case_id=case_id, panel_bed=panel_bed, dry_run=dry_run)
        context.invoke(
            run,
            case_id=case_id,
            priority=priority,
            email=email,
            start_with=start_with,
            dry_run=dry_run,
            mip_dry_run=mip_dry_run,
            skip_evaluation=skip_evaluation,
        )
    except (FlowcellsNeededError, DecompressionNeededError) as e:
        LOG.error(e.message)


@mip_rna.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: MipRNAAnalysisAPI = context.obj["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case_obj in analysis_api.get_cases_to_analyze():
        try:
            context.invoke(start, case_id=case_obj.internal_id, dry_run=dry_run)
        except CgError as error:
            LOG.error(error.message)
            exit_code = EXIT_FAIL
        except Exception as e:
            LOG.error(f"Unspecified error occurred: %s", e)
            exit_code = EXIT_FAIL
    if exit_code:
        raise click.Abort
