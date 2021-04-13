import logging

import click

from cg.cli.workflow.commands import (
    store,
    store_available,
    resolve_compression,
    link,
    ARGUMENT_CASE_ID,
    OPTION_DRY,
)
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.exc import DecompressionNeededError, CgError
from cg.meta.workflow.mutant import MutantAnalysisAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def mutant(context: click.Context) -> None:
    """Covid analysis workflow"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    context.obj["analysis_api"] = MutantAnalysisAPI(
        config=context.obj,
    )


mutant.add_command(resolve_compression)
mutant.add_command(link)
mutant.add_command(store)
mutant.add_command(store_available)


@mutant.command("config-case")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_context
def config_case(context: click.Context, dry_run: bool, case_id: str) -> None:
    """Create config file for a case"""
    analysis_api: MutantAnalysisAPI = context.obj["analysis_api"]
    analysis_api.create_case_config(case_id=case_id, dry_run=dry_run)


@mutant.command("run")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_context
def run(context: click.Context, dry_run: bool, case_id: str) -> None:
    """Run mutant analysis command for a case"""
    analysis_api: MutantAnalysisAPI = context.obj["analysis_api"]
    analysis_api.check_analysis_ongoing(case_id=case_id)
    if not dry_run:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
    try:
        analysis_api.run_analysis(case_id=case_id, dry_run=dry_run)
    except:
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
        raise


@mutant.command("start")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_context
def start(context: click.Context, dry_run: bool, case_id: str) -> None:
    """Start full analysis workflow for a case"""
    try:
        context.invoke(resolve_compression, case_id=case_id, dry_run=dry_run)
        context.invoke(link, case_id=case_id)
        context.invoke(config_case, case_id=case_id, dry_run=dry_run)
        context.invoke(run, case_id=case_id, dry_run=dry_run)
        context.invoke(store, case_id=case_id, dry_run=dry_run)
    except DecompressionNeededError:
        LOG.info("Workflow not ready to run, can continue after decompression")


@mutant.command("start-available")
@OPTION_DRY
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: MutantAnalysisAPI = context.obj["analysis_api"]

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
