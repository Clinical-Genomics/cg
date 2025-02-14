"""Set case attributes in the status database."""

import logging
from typing import Callable

import rich_click as click

from cg.constants import DataDelivery, Priority, Workflow
from cg.constants.constants import CaseActions
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Customer, Panel
from cg.store.store import Store
from cg.utils.click.EnumChoice import EnumChoice

LOG = logging.getLogger(__name__)


@click.command("case")
@click.option("-a", "--action", type=click.Choice(CaseActions.actions()), help="update case action")
@click.option("-c", "--customer-id", type=click.STRING, help="update customer")
@click.option(
    "-d",
    "--data-analysis",
    "data_analysis",
    type=EnumChoice(Workflow),
    help="Update case data analysis",
)
@click.option(
    "-dd",
    "--data-delivery",
    "data_delivery",
    type=EnumChoice(DataDelivery),
    help="Update case data delivery",
)
@click.option("-g", "--panel", "panel_abbreviations", multiple=True, help="update gene panels")
@click.option(
    "-p", "--priority", type=EnumChoice(Priority, use_value=False), help="update priority"
)
@click.argument("case_id")
@click.pass_obj
def set_case(
    context: CGConfig,
    action: str | None,
    data_analysis: Workflow | None,
    data_delivery: DataDelivery | None,
    priority: Priority | None,
    panel_abbreviations: tuple[str] | None,
    case_id: str,
    customer_id: str | None,
):
    """Update information about a case."""

    options: list[str] = [
        action,
        panel_abbreviations,
        priority,
        customer_id,
        data_analysis,
        data_delivery,
    ]
    abort_on_empty_options(options=options, priority=priority)

    status_db: Store = context.status_db
    case: Case = get_case(case_id=case_id, status_db=status_db)

    if action:
        update_action(case=case, action=action)

    if customer_id:
        update_customer(case=case, customer_id=customer_id, status_db=status_db)

    if data_analysis:
        update_data_analysis(case=case, data_analysis=data_analysis)

    if data_delivery:
        update_data_delivery(case=case, data_delivery=data_delivery)

    if panel_abbreviations:
        update_panels(case=case, panel_abbreviations=panel_abbreviations, status_db=status_db)

    if isinstance(priority, Priority):
        update_priority(case=case, priority=priority)

    status_db.session.commit()


def abort_on_empty_options(options: list[str], priority: Priority | None) -> None:
    """Abort if options are empty and bypass_check for priority returns False"""
    if not any(options) and not priority == Priority.research:
        LOG.error("Nothing to change")
        raise click.Abort


def get_case(case_id: str, status_db: Store) -> Case:
    case: Case = status_db.get_case_by_internal_id(internal_id=case_id)

    if case is None:
        LOG.error(f"Can't find case {case_id}")
        raise click.Abort

    return case


def update_action(case: Case, action: str) -> None:
    """Update case action."""
    LOG.info(f"Update action: {case.action or 'NA'} -> {action}")
    case.action = action


def update_customer(case: Case, customer_id: str, status_db: Store) -> None:
    customer_obj: Customer = status_db.get_customer_by_internal_id(customer_internal_id=customer_id)

    if customer_obj is None:
        LOG.error(f"Unknown customer: {customer_id}")
        raise click.Abort

    LOG.info(f"Update customer: {case.customer.internal_id} -> {customer_id}")
    case.customer = customer_obj


def update_data_analysis(case: Case, data_analysis: Workflow) -> None:
    LOG.info(f"Update data_analysis: {case.data_analysis or 'NA'} -> {data_analysis}")
    case.data_analysis = data_analysis


def update_data_delivery(case: Case, data_delivery: DataDelivery) -> None:
    LOG.info(f"Update data_delivery: {case.data_delivery or 'NA'} -> {data_delivery}")
    case.data_delivery = data_delivery


def update_panels(case: Case, panel_abbreviations: list[str], status_db: Store) -> None:
    for panel_abbreviation in panel_abbreviations:
        panel: Panel = status_db.get_panel_by_abbreviation(abbreviation=panel_abbreviation)
        if panel is None:
            LOG.error(f"unknown gene panel: {panel_abbreviation}")
            raise click.Abort
    LOG.info(f"Update panels: {', '.join(case.panels)} -> {', '.join(panel_abbreviations)}")
    case.panels = panel_abbreviations


def update_priority(case: Case, priority: Priority) -> None:
    """Update case priority."""
    LOG.info(f"Update priority: {case.priority.name} -> {priority.name}")
    case.priority = priority
