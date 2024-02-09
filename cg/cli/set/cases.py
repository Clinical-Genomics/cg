import logging

import click

from cg.cli.set.case import set_case
from cg.constants import Priority
from cg.constants.constants import CaseActions
from cg.store.models import Case, Sample
from cg.store.store import Store
from cg.utils.click.EnumChoice import EnumChoice

CONFIRM = "Continue?"

LOG = logging.getLogger(__name__)


def _get_samples_by_identifiers(identifiers: click.Tuple([str, str]), store: Store) -> list[Sample]:
    """Get samples matched by given set of identifiers"""
    identifier_args = dict(identifiers)
    return list(store.get_samples_by_any_id(**identifier_args))


def _get_cases(identifiers: click.Tuple([str, str]), store: Store) -> list[Case]:
    """Get cases that have samples that match identifiers if given"""
    samples_by_id: list[Sample] = _get_samples_by_identifiers(identifiers, store)
    cases: set[Case] = set()
    for sample in samples_by_id:
        for link in sample.links:
            cases.add(link.case)

    return list(cases)


@click.command("cases")
@click.option(
    "--sample-identifier",
    "identifiers",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help="Give an identifier on sample and the value to use it with, e.g. --sample-identifier "
    "name Prov52",
)
@click.option("-a", "--action", type=click.Choice(CaseActions.actions()), help="update case action")
@click.option("-c", "--customer-id", type=click.STRING, help="update customer")
@click.option("-g", "--panel", "panel_abbreviations", multiple=True, help="update gene panels")
@click.option(
    "-p", "--priority", type=EnumChoice(Priority, use_value=False), help="update priority"
)
@click.pass_context
def set_cases(
    context: click.Context,
    action: str | None,
    priority: Priority | None,
    panel_abbreviations: tuple[str] | None,
    customer_id: str | None,
    identifiers: click.Tuple([str, str]),
):
    """Set values on many families at the same time"""
    store: Store = context.obj.status_db
    cases_to_alter: list[Case] = _get_cases(identifiers, store)

    if not cases_to_alter:
        LOG.error("No cases to alter!")
        raise click.Abort

    LOG.info("Would alter cases:")

    for case_to_alter in cases_to_alter:
        LOG.info(case_to_alter)

    if not (click.confirm(CONFIRM)):
        raise click.Abort

    for case_to_alter in cases_to_alter:
        context.invoke(
            set_case,
            action=action,
            priority=priority,
            panel_abbreviations=panel_abbreviations,
            case_id=case_to_alter.internal_id,
            customer_id=customer_id,
        )
