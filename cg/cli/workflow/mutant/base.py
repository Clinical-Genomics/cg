import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import (
    ARGUMENT_CASE_ID,
    OPTION_ANALYSIS_PARAMETERS_CONFIG,
    link,
    resolve_compression,
    store,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.constants.cli_options import DRY_RUN
from cg.exc import AnalysisNotReadyError, CgError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.mutant import MutantAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case

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

    try:
        analysis_api.run_analysis(case_id=case_id, dry_run=dry_run, config_artic=config_artic)
        if not dry_run:
            analysis_api.on_analysis_started(case_id=case_id)
    except Exception as error:
        LOG.error(f"Error running analysis for case {case_id}: {error}")
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


@mutant.command("store-available")
@DRY_RUN
@click.pass_context
def store_available(context: click.Context, dry_run: bool) -> None:
    """Run QC checks and store bundles for all finished analyses in Housekeeper."""

    analysis_api: MutantAnalysisAPI = context.obj.meta_apis["analysis_api"]

    exit_code: int = EXIT_SUCCESS

    cases_ready_for_qc: list[Case] = analysis_api.get_cases_to_perform_qc_on()
    LOG.info(f"Found {len(cases_ready_for_qc)} cases to perform QC on!")
    for case in cases_ready_for_qc:
        LOG.info(f"Performing QC on case {case.internal_id}.")
        try:
            analysis_api.run_qc_on_case(case=case, dry_run=dry_run)
        except Exception:
            exit_code = EXIT_FAIL

    cases_to_store: list[Case] = analysis_api.get_cases_to_store()
    LOG.info(f"Found {len(cases_to_store)} cases to store!")
    for case in cases_to_store:
        LOG.info(f"Storing deliverables for {case.internal_id}")
        try:
            context.invoke(store, case_id=case.internal_id, dry_run=dry_run)
        except Exception as exception_object:
            LOG.error(f"Error storingc {case.internal_id}: {exception_object}")
            exit_code = EXIT_FAIL

    if exit_code:
        raise click.Abort


@mutant.command("run-qc")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_context
def run_qc(context: click.Context, case_id: str, dry_run: bool) -> None:
    """
    Run QC on case and generate QC_report file.
    """
    analysis_api: MutantAnalysisAPI = context.obj.meta_apis["analysis_api"]

    analysis_api.run_qc(case_id=case_id, dry_run=dry_run)
