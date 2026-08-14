import logging

import rich_click as click

from cg.cli.set.case import set_case
from cg.constants import Priority
from cg.constants.constants import CaseActions
from cg.store.models import Case, Sample
from cg.store.store import Store
from cg.utils.click.EnumChoice import EnumChoice

CONFIRM = "Continue?"

LOG = logging.getLogger(__name__)


def _get_samples_by_identifiers(
    sample_identifiers: list[tuple[str, str]], store: Store
) -> list[Sample]:
    """Get samples matched by given set of identifiers"""
    identifier_args = dict(sample_identifiers)
    return list(store.get_samples_by_any_id(identifier_args))


def _get_cases(
    case_ids: tuple[str], sample_identifiers: list[tuple[str, str]], store: Store
) -> set[Case]:
    """Get cases that have samples that match identifiers if given"""
    cases: set[Case] = set()
    if sample_identifiers:
        samples_by_id: list[Sample] = _get_samples_by_identifiers(
            sample_identifiers=sample_identifiers, store=store
        )
        for sample in samples_by_id:
            for link in sample.links:
                cases.add(link.case)
    cases = cases.union(set(store.get_cases_by_internal_ids(list(case_ids))))
    return cases


@click.command("cases")
@click.option(
    "--sample-identifier",
    "sample_identifiers",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    required=False,
    help="Give an identifier on sample and the value to use it with, e.g. --sample-identifier "
    "name Prov52",
)
@click.option(
    "--case-id",
    "case_ids",
    multiple=True,
    required=False,
    help="Give a list of case internal ids on which to perform the action, e.g. --case-id case_1 --case-id case_2",
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
    case_ids: tuple[str] | None,
    sample_identifiers: list[tuple[str, str]] | None,
    action: str | None,
    priority: Priority | None,
    panel_abbreviations: tuple[str] | None,
    customer_id: str | None,
):
    """Set values on many families at the same time"""
    if not case_ids and not sample_identifiers:
        LOG.error("You must provide either case ids or sample identifiers")
        raise click.Abort

    store: Store = context.obj.status_db
    cases_to_alter: set[Case] = _get_cases(
        case_ids=case_ids, sample_identifiers=sample_identifiers, store=store
    )

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
