import logging

import click
import datetime as dt
from cgmodels.cg.constants import Pipeline

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.constants.constants import DRY_RUN
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
def fastq(context: click.Context):
    """Function for storing fastq-cases"""
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
    return None


@fastq.command("store")
@DRY_RUN
@ARGUMENT_CASE_ID
@click.pass_context
def store_fastq_analysis(context: click.Context, case_id: str, dry_run: bool = False):
    """Creates an analysis object in status-db for the given fast case"""
    LOG.info("Creating an analysis for case %s", case_id)
    status_db: Store = context.obj.status_db
    case_obj: models.Family = status_db.family(internal_id=case_id)
    new_analysis: models.Analysis = status_db.add_analysis(
        pipeline=Pipeline.FASTQ,
        completed_at=dt.datetime.now(),
        primary=True,
        started_at=dt.datetime.now(),
        family_id=case_obj.id,
    )
    if dry_run:
        return
    status_db.add_commit(new_analysis)


@fastq.command("store-available")
@DRY_RUN
@click.pass_context
def store_available_fastq_analysis(context: click.Context, dry_run: bool = False):
    """Creates an analysis object in status-db for all fastq cases to be delivered"""
    status_db: Store = context.obj.status_db
    for case in status_db.cases_to_analyze(pipeline=Pipeline.FASTQ, threshold=False):
        if case.all_samples_pass_qc or status_db.is_pool(case_id=case.internal_id):
            context.invoke(store_fastq_analysis, case_id=case.internal_id, dry_run=dry_run)
