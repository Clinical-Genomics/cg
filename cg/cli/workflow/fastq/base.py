import logging

import click

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.cli.workflow.fastq.fastq_service import FastqService
from cg.constants.constants import DRY_RUN, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.services.quality_controller import QualityControllerService
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def fastq(context: click.Context):
    """Function for storing fastq-cases"""
    AnalysisAPI.get_help(context)


@fastq.command("store")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_context
def store_fastq_analysis(context: click.Context, case_id: str, dry_run: bool = False):
    LOG.info(f"Creating an analysis for case {case_id}")

    if dry_run:
        return

    fastq_service = FastqService(
        store=context.obj.status_db,
        trailblazer_api=context.obj.trailblazer_api,
    )
    fastq_service.store_analysis(case_id)


@fastq.command("store-available")
@DRY_RUN
@click.pass_context
def store_available_fastq_analysis(context: click.Context, dry_run: bool = False):
    """Creates an analysis object in status-db for all fastq cases to be delivered."""
    status_db: Store = context.obj.status_db
    for case in status_db.cases_to_analyse(workflow=Workflow.FASTQ):
        if QualityControllerService.case_pass_sequencing_qc(case):
            context.invoke(store_fastq_analysis, case_id=case.internal_id, dry_run=dry_run)
