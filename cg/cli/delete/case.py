"""CLI for deleting case with Cg."""

import datetime
import logging

import click

from cg.cli.get import get_case as print_case
from cg.constants.cli_options import DRY_RUN, SKIP_CONFIRMATION
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("case")
@click.argument("case_id")
@DRY_RUN
@SKIP_CONFIRMATION
@click.pass_context
def delete_case(context: click.Context, case_id: str, dry_run: bool, yes: bool):
    """Delete case with links and samples.

    The command will stop if the case has any analyses made on it.
    The command will ask the user about deleting links between case and samples
    If a sample has its last link removed the command will ask about deleting the sample
    The command will not delete samples that has been processed (received etc.)
    The command will not delete a sample that has been marked as mother or father to another
    sample.
    """
    status_db: Store = context.obj.status_db
    case: Case = status_db.get_case_by_internal_id(internal_id=case_id)
    if not case:
        LOG.error(f"Could not find case {case_id}")
        raise click.Abort

    if case.analyses:
        LOG.error(f"Can NOT delete case with analyses {case.analyses}")
        raise click.Abort
    context.invoke(print_case, case_ids=[case_id])

    if case.links and not (
        yes or click.confirm(f"Case {case_id} has links: {case.links}, continue?")
    ):
        raise click.Abort

    _delete_links_and_samples(case_obj=case, dry_run=dry_run, status_db=status_db, yes=yes)

    if not (yes or click.confirm(f"Do you want to DELETE case: {case}?")):
        raise click.Abort

    if dry_run:
        LOG.info(f"Case: {case_id} was NOT deleted due to --dry-run")
        return

    LOG.info(f"Deleting case: {case_id}")
    status_db.session.delete(case)
    status_db.session.commit()


def _delete_links_and_samples(case_obj: Case, dry_run: bool, status_db: Store, yes: bool):
    """Delete all links from a case to samples"""
    samples_to_delete: list[Sample] = []
    for case_link in case_obj.links:
        if not (yes or click.confirm(f"Do you want to DELETE link: {case_link}?")):
            raise click.Abort

        samples_to_delete.append(case_link.sample)

        if dry_run:
            LOG.info(f"Link: {case_link} was NOT deleted due to --dry-run")
        else:
            LOG.info(f"Deleting link: {case_link}")
            status_db.session.delete(case_link)
            status_db.session.commit()

    for sample in samples_to_delete:
        _delete_sample(dry_run=dry_run, sample=sample, status_db=status_db, yes=yes)


def _delete_sample(dry_run: bool, sample: Sample, status_db: Store, yes: bool):
    if _has_sample_been_lab_processed(sample):
        _log_sample_process_information(sample)
        return

    if _is_sample_linked(sample):
        LOG.info(f"Can NOT delete sample: {sample.internal_id}")
        _log_sample_links(sample)
        return

    if not (
        yes
        or click.confirm(
            f"Sample {sample.internal_id} is not linked to anything, "
            f"do you want to DELETE sample:"
            f" {sample}?"
        )
    ):
        return

    if dry_run:
        LOG.info(f"Sample: {sample} was NOT deleted due to --dry-run")
        return

    LOG.info(f"Deleting sample: {sample}")
    status_db.session.delete(sample)


def _log_sample_process_information(sample: Sample):
    LOG.info(f"Can NOT delete processed sample: {sample.internal_id}")
    LOG.info(f"Sample was received: {sample.received_at}")
    LOG.info(f"Sample was prepared: {sample.prepared_at}")
    LOG.info(f"Sample's reads were updated: {sample.last_sequenced_at}")
    LOG.info(f"Sample was delivered: {sample.delivered_at}")
    LOG.info(f"Sample has invoice: {sample.invoice_id}")


def _log_sample_links(sample: Sample):
    for sample_link in sample.links:
        LOG.info(f"Sample is linked to: {sample_link.case.internal_id}")
    for sample_link in sample.mother_links:
        LOG.info(f"Sample is linked as mother to: {sample_link.mother.internal_id}")
    for sample_link in sample.father_links:
        LOG.info(f"Sample is linked as father to: {sample_link.father.internal_id}")


def _has_sample_been_lab_processed(sample: Sample) -> datetime.datetime:
    return (
        sample.received_at
        or sample.prepared_at
        or sample.last_sequenced_at
        or sample.delivered_at
        or sample.invoice_id
    )


def _is_sample_linked(sample: Sample):
    return sample.links or sample.father_links or sample.mother_links
