"""Set case attributes in the status database."""
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
    status_db: Store = context.status_db
    case: Family = status_db.family(family_id)
    if case is None:
        LOG.error(f"Can not find case {family_id}")
        raise click.Abort
    if not any([action, panels, priority, customer_id, data_analysis, data_delivery]):
        LOG.error("Nothing to change")
        raise click.Abort
    if action:
        LOG.info(f"Update action: {case.action or 'NA'} -> {action}")
        case.action = action
    if customer_id:
        customer: Customer = status_db.get_customer_by_customer_id(customer_id=customer_id)
        if customer is None:
            LOG.error(f"Unknown customer: {customer_id}")
            raise click.Abort
        LOG.info(f"Update customer: {case.customer.internal_id} -> {customer_id}")
        case.customer = customer
    if data_analysis:
        LOG.info(f"Update data_analysis: {case.data_analysis or 'NA'} -> {data_analysis}")
        case.data_analysis = data_analysis
    if data_delivery:
        LOG.info(f"Update data_delivery: {case.data_delivery or 'NA'} -> {data_delivery}")
        case.data_delivery = data_delivery
    if panels:
        for panel_abbreviation in panels:
            panel: Panel = status_db.get_panel_by_abbreviation(abbreviation=panel_abbreviation)
            if panel is None:
                LOG.error(f"Unknown gene panel: {panel_abbreviation}")
                raise click.Abort
        LOG.info(f"Update panels: {', '.join(case.panels)} -> {', '.join(panels)}")
        case.panels = panels
    if priority:
        LOG.info(f"Update priority: {case.priority.name} -> {priority.name}")
        case.priority = priority
    status_db.commit()
