import logging

import click
import datetime as dt
from cgmodels.cg.constants import Pipeline

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.constants.constants import DRY_RUN
from cg.store import Store
from cg.store.models import Analysis, Family
from cg.meta.workflow.analysis import AnalysisAPI

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
    """Creates an analysis object in status-db for the given fast case"""
    LOG.info("Creating an analysis for case %s", case_id)
    status_db: Store = context.obj.status_db
    case_obj: Family = status_db.get_case_by_internal_id(internal_id=case_id)
    new_analysis: Analysis = status_db.add_analysis(
        pipeline=Pipeline.FASTQ,
        completed_at=dt.datetime.now(),
        primary=True,
        started_at=dt.datetime.now(),
        family_id=case_obj.id,
    )
    if dry_run:
        return
    status_db.session.add(new_analysis)
    status_db.session.commit()


@fastq.command("store-available")
@DRY_RUN
@click.pass_context
def store_available_fastq_analysis(context: click.Context, dry_run: bool = False):
    """Creates an analysis object in status-db for all fastq cases to be delivered"""
    status_db: Store = context.obj.status_db
    for case in status_db.cases_to_analyze(pipeline=Pipeline.FASTQ, threshold=False):
        context.invoke(store_fastq_analysis, case_id=case.internal_id, dry_run=dry_run)
