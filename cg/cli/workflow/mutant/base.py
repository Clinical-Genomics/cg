import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import (
    ARGUMENT_CASE_ID,
    OPTION_ANALYSIS_PARAMETERS_CONFIG,
    link,
    resolve_compression,
    store,
    store_available,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import DRY_RUN
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def mutant(context: click.Context) -> None:
    """Mutant analysis workflow"""
    AnalysisAPI.get_help(context)
    context.obj.meta_apis["analysis_api"] = MutantAnalysisAPI(config=context.obj)


mutant.add_command(resolve_compression)
mutant.add_command(link)
mutant.add_command(store)
mutant.add_command(store_available)


@mutant.command("config-case")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def config_case(context: CGConfig, dry_run: bool, case_id: str) -> None:
    """Create config file for a case"""
    analysis_api: MutantAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.create_case_config(case_id=case_id, dry_run=dry_run)


@mutant.command("run")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_obj
def run(context: CGConfig, dry_run: bool, case_id: str, config_artic: str = None) -> None:
    """Run mutant analysis command for a case"""
    analysis_api: MutantAnalysisAPI = context.meta_apis["analysis_api"]
    analysis_api.check_analysis_ongoing(case_id=case_id)
    if not dry_run:
        analysis_api.add_pending_trailblazer_analysis(case_id=case_id)
        analysis_api.set_statusdb_action(case_id=case_id, action="running")
    try:
        analysis_api.run_analysis(case_id=case_id, dry_run=dry_run, config_artic=config_artic)
    except:
        analysis_api.set_statusdb_action(case_id=case_id, action=None)
        raise


@mutant.command("start")
@DRY_RUN
@ARGUMENT_CASE_ID
@OPTION_ANALYSIS_PARAMETERS_CONFIG
@click.pass_context
def start(context: click.Context, dry_run: bool, case_id: str, config_artic: str) -> None:
    """Start full analysis workflow for a case"""
    analysis_api: MutantAnalysisAPI = context.obj.meta_apis["analysis_api"]
    analysis_api.prepare_fastq_files(case_id=case_id, dry_run=dry_run)
    context.invoke(link, case_id=case_id, dry_run=dry_run)
    context.invoke(config_case, case_id=case_id, dry_run=dry_run)
    context.invoke(run, case_id=case_id, dry_run=dry_run, config_artic=config_artic)
    context.invoke(store, case_id=case_id, dry_run=dry_run)


@mutant.command("start-available")
@DRY_RUN
@click.pass_context
def start_available(context: click.Context, dry_run: bool = False):
    """Start full analysis workflow for all cases ready for analysis"""

    analysis_api: MutantAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS
    for case in analysis_api.get_cases_ready_for_analysis():
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
