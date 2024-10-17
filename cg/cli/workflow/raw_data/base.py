import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.cli.workflow.raw_data.raw_data_service import RawDataAnalysisService
from cg.constants.cli_options import DRY_RUN
from cg.constants.constants import Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.services.sequencing_qc_service import SequencingQCService
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_context
def raw_data(context: click.Context):
    """Function for storing raw-data-cases"""
    AnalysisAPI.get_help(context)


@raw_data.command("store")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_context
def store_raw_data_analysis(context: click.Context, case_id: str, dry_run: bool = False):
    LOG.info(f"Creating an analysis for case {case_id}")

    if dry_run:
        return

    raw_data_service = RawDataAnalysisService(
        store=context.obj.status_db,
        trailblazer_api=context.obj.trailblazer_api,
    )
    raw_data_service.store_analysis(case_id)


@raw_data.command("store-available")
@DRY_RUN
@click.pass_context
def store_available_raw_data_analysis(context: click.Context, dry_run: bool = False):
    """Creates an analysis object in status-db for all raw data cases to be delivered."""
    status_db: Store = context.obj.status_db
    for case in status_db.cases_to_analyse(workflow=Workflow.RAW_DATA):
        LOG.info(f"Creating an analysis for case {case.internal_id}")
        if SequencingQCService.case_pass_sequencing_qc(case):
            if dry_run:
                return
            raw_data_service = RawDataAnalysisService(
                store=context.obj.status_db,
                trailblazer_api=context.obj.trailblazer_api,
            )
            raw_data_service.store_analysis(case.internal_id)
