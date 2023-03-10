"""Set case attributes in the status database"""
import logging
from typing import Optional, Tuple
import click

from cg.constants import CASE_ACTIONS, DataDelivery, Pipeline
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Customer, Family, Panel
from cg.utils.click.EnumChoice import EnumChoice

from cg.constants import Priority

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-a", "--action", type=click.Choice(CASE_ACTIONS), help="update case action")
@click.option("-c", "--customer-id", type=click.STRING, help="update customer")
@click.option(
    "-d",
    "--data-analysis",
    "data_analysis",
    type=EnumChoice(Pipeline),
    help="Update case data analysis",
)
@click.option(
    "-dd",
    "--data-delivery",
    "data_delivery",
    type=EnumChoice(DataDelivery),
    help="Update case data delivery",
)
@click.option("-g", "--panel", "panels", multiple=True, help="update gene panels")
@click.option(
    "-p", "--priority", type=EnumChoice(Priority, use_value=False), help="update priority"
)
@click.argument("family_id")
@click.pass_obj
def family(
    context: CGConfig,
    action: Optional[str],
    data_analysis: Optional[Pipeline],
    data_delivery: Optional[DataDelivery],
    priority: Optional[Priority],
    panels: Optional[Tuple[str]],
    family_id: str,
    customer_id: Optional[str],
):
    """Update information about a case."""

    check_nothing_to_change(action, panels, priority, customer_id, data_analysis, data_delivery)

    status_db: Store = context.status_db
    case: Family = get_case(family_id, status_db)

    if action:
        update_action(case, action)

    if customer_id:
        update_customer(case, customer_id, status_db)

    if data_analysis:
        update_data_analysis(case, data_analysis)

    if data_delivery:
        update_data_delivery(case, data_delivery)

    if panels:
        update_panels(case, panels, status_db)

    if priority:
        update_priority(case, priority)

    status_db.commit()


def check_nothing_to_change(action, panels, priority, customer_id, data_analysis, data_delivery):
    if not any([action, panels, priority, customer_id, data_analysis, data_delivery]):
        LOG.error("Nothing to change")
        raise click.Abort


def get_case(case_id: str, status_db: Store):
    case: Family = status_db.family(case_id)

    if case is None:
        LOG.error(f"Can't find case {case_id}")
        raise click.Abort

    return case


def update_action(case: Family, action: str) -> None:
    """Update case action."""
    LOG.info(f"Update action: {case.action or 'NA'} -> {action}")
    case.action = action


def update_customer(case: Family, customer_id: str, status_db: Store):
    customer_obj: Customer = status_db.customer(customer_id)

    if customer_obj is None:
        LOG.error("Unknown customer: %s", customer_id)
        raise click.Abort

    LOG.info(f"Update customer: {case.customer.internal_id} -> {customer_id}")
    case.customer = customer_obj


def update_data_analysis(case: Family, data_analysis: Pipeline):
    LOG.info(f"Update data_analysis: {case.data_analysis or 'NA'} -> {data_analysis}")
    case.data_analysis = data_analysis


def update_data_delivery(case: Family, data_delivery: DataDelivery):
    LOG.info(f"Update data_delivery: {case.data_delivery or 'NA'} -> {data_delivery}")
    case.data_delivery = data_delivery


def update_panels(case, panels, status_db):
    for panel_id in panels:
        panel: Panel = status_db.panel(panel_id)
        if panel is None:
            LOG.error(f"unknown gene panel: {panel_id}")
            raise click.Abort
    LOG.info(f"Update panels: {', '.join(case.panels)} -> {', '.join(panels)}")
    case.panels = panels


def update_priority(case: Family, priority: Priority) -> None:
    """Update case priority."""
    LOG.info(f"Update priority: {case.priority.name} -> {priority.name}")
    case.priority = priority
