import logging

import click
from cg.cli.workflow.commands import (
    ARGUMENT_CASE_ID,
    OPTION_DRY,
    link,
    resolve_compression,
    store,
    store_available,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.exc import CgError, DecompressionNeededError
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def mutant(context: click.Context) -> None:
    """Covid analysis workflow"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
    context.obj.meta_apis["analysis_api"] = MutantAnalysisAPI(
        config=context.obj,
    )


mutant.add_command(resolve_compression)
mutant.add_command(link)
mutant.add_command(store)
mutant.add_command(store_available)


@mutant.command("config-case")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(context: CGConfig, dry_run: bool, case_id: str) -> None:
    """Create config file for a case"""
    analysis_api: MutantAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.create_case_config(case_id=case_id, dry_run=dry_run)


@mutant.command("run")
@OPTION_DRY
@ARGUMENT_CASE_ID
@click.pass_obj
def run(context: CGConfig, dry_run: bool, case_id: str) -> None:
    """Run mutant analysis command for a case"""
    analysis_api: MutantAnalysisAPI = context.meta_apis["analysis_api"]
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
@click.option("--force", is_flag=True)
@click.pass_context
def start(context: click.Context, dry_run: bool, case_id: str, force: bool) -> None:
    """Start full analysis workflow for a case"""
    if not force:
        analysis_api: MutantAnalysisAPI = context.obj.meta_apis["analysis_api"]
        are_NTCs_clean: bool = analysis_api.check_if_NTCs_are_clean(case_id=case_id)
        if not are_NTCs_clean:
            LOG.error("Analysis won't start, a negative control is contaminated")
            return
    try:
        context.invoke(link, case_id=case_id, dry_run=dry_run)
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

    analysis_api: MutantAnalysisAPI = context.obj.meta_apis["analysis_api"]

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
