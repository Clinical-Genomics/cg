"""CLI for deleting case with CG"""

import logging

import click
from cg.cli.get import family as print_case
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("case_id")
@click.option("--dry-run", is_flag=True)
@click.option("--yes", is_flag=True)
@click.pass_context
def case(context, case_id: str, dry_run: bool, yes: bool):
    """Delete case with links and samples

    The command will stop if the case has any analyses made on it.
    The command will ask the user about deleting links between case and samples
    If a sample has its last link removed the command will ask about deleting the sample
    The command will not delete samples that has been processed (received etc.)
    The command will not delete a sample that has been marked as mother or father to another
    sample.
    """
    status_db: Store = context.obj["status_db"]
    case_obj = status_db.family(case_id)
    if not case_obj:
        LOG.error("Could not find case %s", case_id)
        context.abort()

    if case_obj.analyses:
        LOG.error("Can't delete case with analyses %s", case_obj.analyses)
        context.abort()

    context.invoke(print_case, family_ids=[case_id])

    if case_obj.links and not (
        yes or click.confirm(f"Case {case_id} has links: {case_obj.links}, Continue?")
    ):
        context.abort()

    _delete_links_and_samples(case_obj, context, dry_run, status_db, yes)

    if not (yes or click.confirm(f"Do you want to delete case: {case_obj}?")):
        context.abort()

    LOG.info("Deleting case: %s", case_id)

    if not dry_run:
        status_db.delete_commit(case_obj)


def _delete_links_and_samples(case_obj, context, dry_run, status_db, yes):
    """Delete all links from a case to samples"""
    for case_link in case_obj.links:
        sample = case_link.sample
        if not (yes or click.confirm(f"Do you want to delete link: {case_link}?")):
            context.abort()
        else:
            LOG.info("Deleting link: %s", case_link)
            if not dry_run:
                status_db.delete_commit(case_link)

        _delete_sample(dry_run, sample, status_db, yes)


def _delete_sample(dry_run, sample, status_db, yes):
    if _has_sample_been_processed(sample):
        _log_sample_process_information(sample)
        return

    if _is_sample_linked(sample):
        LOG.info("Can't delete sample: %s", sample.internal_id)
        _log_sample_links(sample)
        return

    if yes or click.confirm(
        f"Sample {sample.internal_id} is not linked to anything, "
        f"do you want to delete sample:"
        f" {sample}?"
    ):
        LOG.info("Deleting sample: %s", sample)
        if not dry_run:
            status_db.delete(sample)


def _log_sample_process_information(sample):
    LOG.info("Can't delete processed sample: %s", sample.internal_id)
    LOG.info("sample was received: %s", sample.received_at)
    LOG.info("sample was prepared: %s", sample.prepared_at)
    LOG.info("sample was sequenced: %s", sample.sequenced_at)
    LOG.info("sample was delivered: %s", sample.delivered_at)
    LOG.info("sample has invoice: %s", sample.invoice_id)


def _log_sample_links(sample):
    for sample_link in sample.links:
        LOG.info("sample is linked to: %s", sample_link.family.internal_id)
    for sample_link in sample.mother_links:
        LOG.info("sample is linked as mother to: %s", sample_link.mother.internal_id)
    for sample_link in sample.father_links:
        LOG.info("sample is linked as father to: %s", sample_link.father.internal_id)


def _has_sample_been_processed(sample: models.Sample):
    return (
        sample.received_at
        or sample.prepared_at
        or sample.sequenced_at
        or sample.delivered_at
        or sample.invoice_id
    )


def _is_sample_linked(sample: models.Sample):
    return sample.links or sample.father_links or sample.mother_links
