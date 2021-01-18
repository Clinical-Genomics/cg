"""CLI for deleting case with CG"""

import logging
import click

from cg.store import Store
from cg.store.models import Family

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("case_id")
@click.option("--dry-run", is_flag=True)
@click.option("--yes", is_flag=True)
@click.pass_context
def case(context, case_id: str, dry_run: bool, yes: bool):
    """Delete case with links and samples"""
    if not case_id:
        LOG.info("Please provide a case-id")
        context.abort()

    status_db: Store = context.obj["status_db"]
    case_obj = status_db.family(case_id)
    if not case_obj:
        LOG.warning("Could not find case %s", case_id)
        context.abort()

    for case_link in case_obj.links:
        sample = case_link.sample
        if not (
            yes
            or click.confirm(
                f"Do you want to delete link between {case_id} and sample:" f" {sample}?"
            )
        ):
            context.abort()
        else:
            if not dry_run:
                status_db.delete(case_link)

        if not sample.links:
            if yes or click.confirm(
                f"Sample {sample.internal_id} is not linked to anything, "
                f"do you want to delete sample:"
                f" {sample}?"
            ):
                if not dry_run:
                    status_db.delete(sample)
        else:
            LOG.info("Can't delete sample: %s", sample.internal_id)
            for sample_link in sample.links:
                LOG.info("sample is linked to: %s", sample_link.family.internal_id)

    if not (yes or click.confirm(f"Do you want to delete case: {case_obj}?")):
        context.abort()

    LOG.info("Deleting case: %s", case_id)

    if not dry_run:
        status_db.delete(case_obj)
