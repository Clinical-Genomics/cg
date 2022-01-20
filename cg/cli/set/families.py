import logging
from typing import List, Optional, Set, Tuple

import click
from cg.constants import CASE_ACTIONS
from cg.store import Store, models

from .family import family
from ...constants import Priority
from ...utils.click.EnumChoice import EnumChoice

CONFIRM = "Continue?"

LOG = logging.getLogger(__name__)


def _get_samples_by_identifiers(
    identifiers: click.Tuple([str, str]), store: Store
) -> List[models.Sample]:
    """Get samples matched by given set of identifiers"""
    identifier_args = dict(identifiers)
    return list(store.samples_by_ids(**identifier_args))


def _get_cases(identifiers: click.Tuple([str, str]), store: Store) -> List[models.Family]:
    """Get cases that have samples that match identifiers if given"""
    samples_by_id: List[models.Sample] = _get_samples_by_identifiers(identifiers, store)
    cases: Set[models.Family] = set()
    for sample in samples_by_id:
        for link in sample.links:
            cases.add(link.family)

    return list(cases)


@click.command()
@click.option(
    "--sample-identifier",
    "identifiers",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help="Give an identifier on sample and the value to use it with, e.g. --sample-identifier "
    "name Prov52",
)
@click.option("-a", "--action", type=click.Choice(CASE_ACTIONS), help="update family action")
@click.option("-c", "--customer-id", type=click.STRING, help="update customer")
@click.option("-g", "--panel", "panels", multiple=True, help="update gene panels")
@click.option(
    "-p", "--priority", type=EnumChoice(Priority, use_value=False), help="update priority"
)
@click.pass_context
def families(
    context: click.Context,
    action: Optional[str],
    priority: Optional[Priority],
    panels: Optional[Tuple[str]],
    customer_id: Optional[str],
    identifiers: click.Tuple([str, str]),
):
    """Set values on many families at the same time"""
    store: Store = context.obj.status_db
    cases: List[models.Family] = _get_cases(identifiers, store)

    if not cases:
        LOG.error("No cases to alter!")
        raise click.Abort

    LOG.info("Would alter cases:")

    for case in cases:
        LOG.info(case)

    if not (click.confirm(CONFIRM)):
        raise click.Abort

    for case in cases:
        context.invoke(
            family,
            action=action,
            priority=priority,
            panels=panels,
            family_id=case.internal_id,
            customer_id=customer_id,
        )
