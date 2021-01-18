"""CLI for deleting case with CG"""

import logging
import click

from cg.store import Store

LOG = logging.getLogger(__name__)


def _delete_analyses(case_obj, context, dry_run, status_db, yes):
    """Delete all analyses of a case"""
    for case_analysis in case_obj.analyses:
        if not (
            yes
            or click.confirm(
                f"Do you want to delete {case_analysis.pipeline} analysis of {case_analysis}?"
            )
        ):
            context.abort()
        else:
            LOG.info("Deleting analysis: %s", case_analysis)
            if not dry_run:
                status_db.delete_commit(case_analysis)


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

    _delete_links_and_samples(case_obj, context, dry_run, status_db, yes)
    _delete_analyses(case_obj, context, dry_run, status_db, yes)

    if not (yes or click.confirm(f"Do you want to delete case: {case_obj}?")):
        context.abort()

    LOG.info("Deleting case: %s", case_id)

    if not dry_run:
        status_db.delete_commit(case_obj)


def _delete_links_and_samples(case_obj, context, dry_run, status_db, yes):
    """Delete all links from a case to samples"""
    case_id = case_obj.internal_id
    for case_link in case_obj.links:
        sample = case_link.sample
        if not (
            yes
            or click.confirm(
                f"Do you want to delete link {case_link}?"
            )
        ):
            context.abort()
        else:
            LOG.info("Deleting link: %s", case_link)
            if not dry_run:
                status_db.delete_commit(case_link)

        _delete_sample(dry_run, sample, status_db, yes)


def _delete_sample(dry_run, sample, status_db, yes):

    if not sample.links and not sample.father_links and not sample.mother_links:

        if yes or click.confirm(
                f"Sample {sample.internal_id} is not linked to anything, "
                f"do you want to delete sample:"
                f" {sample}?"
        ):
            LOG.info("Deleting sample: %s", sample)
            if not dry_run:
                status_db.delete(sample)
    else:
        LOG.info("Can't delete sample: %s", sample.internal_id)
        for sample_link in sample.links:
            LOG.info("sample is linked to: %s", sample_link.family.internal_id)
        for sample_link in sample.mother_links:
            LOG.info("sample is linked as mother to: %s", sample_link.mother.internal_id)
        for sample_link in sample.father_links:
            LOG.info("sample is linked as father to: %s", sample_link.father.internal_id)
