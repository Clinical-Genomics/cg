import logging

import click
from cg.store import Store
from cg.store.models import Family, Sample

from cg.cli.delete.case import delete_case

CONFIRM = "Continue?"

LOG = logging.getLogger(__name__)


def _get_samples_by_identifiers(identifiers: click.Tuple([str, str]), store: Store) -> [Sample]:
    """Get samples matched by given set of identifiers"""
    identifier_args = dict(identifiers)
    return store.get_samples_by_any_id(**identifier_args)


def _get_cases(identifiers: click.Tuple([str, str]), store: Store) -> [Family]:
    """Get cases that have samples that match identifiers if given"""
    samples_by_id = _get_samples_by_identifiers(identifiers, store)
    _cases = set()
    for sample in samples_by_id:
        for link in sample.links:
            _cases.add(link.family)

    return _cases


@click.command("cases")
@click.option("--dry-run", is_flag=True)
@click.option(
    "--sample-identifier",
    "identifiers",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help="Give an identifier on sample and the value to use it with, e.g. --sample-identifier "
    "name Prov52",
)
@click.pass_context
def delete_cases(
    context: click.Context,
    dry_run: bool,
    identifiers: click.Tuple([str, str]),
):
    """Delete many cases of samples at the same time"""
    store = context.obj.status_db
    _cases = _get_cases(identifiers, store)

    if not _cases:
        LOG.error("No cases to delete!")
        raise click.Abort

    if dry_run:
        LOG.info("Cases (that will NOT be deleted due to --dry-run):")
    else:
        LOG.info("Would DELETE cases:")

    for _case in _cases:
        LOG.info(_case)

    if not (click.confirm(CONFIRM)):
        raise click.Abort

    for _case in _cases:
        context.invoke(
            delete_case,
            case_id=_case.internal_id,
            dry_run=dry_run,
        )
