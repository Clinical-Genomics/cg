"""Set family attributes in the status database"""
import logging

import click
from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-a", "--action", type=click.Choice(FAMILY_ACTIONS), help="update family action")
@click.option("-c", "--customer-id", type=click.STRING, help="update customer")
@click.option("-g", "--panel", "panels", multiple=True, help="update gene panels")
@click.option("-p", "--priority", type=click.Choice(PRIORITY_OPTIONS), help="update priority")
@click.argument("family_id")
@click.pass_context
def family(
    context: click.Context,
    action: str,
    priority: str,
    panels: [str],
    family_id: str,
    customer_id: str,
):
    """Update information about a family."""

    family_obj = context.obj["status_db"].family(family_id)
    if family_obj is None:
        LOG.error("Can't find family %s,", family_id)
        raise click.Abort
    if not any([action, panels, priority, customer_id]):
        LOG.error("Nothing to change")
        raise click.Abort
    if action:
        LOG.info(f"Update action: {family_obj.action or 'NA'} -> {action}")
        family_obj.action = action
    if customer_id:
        customer_obj = context.obj["status_db"].customer(customer_id)
        if customer_obj is None:
            LOG.error("Unknown customer: %s", customer_id)
            raise click.Abort
        LOG.info(f"Update customer: {family_obj.customer.internal_id} -> {customer_id}")
        family_obj.customer = customer_obj
    if panels:
        for panel_id in panels:
            panel_obj = context.obj["status_db"].panel(panel_id)
            if panel_obj is None:
                LOG.error(f"unknown gene panel: {panel_id}")
                raise click.Abort
        LOG.info(f"Update panels: {', '.join(family_obj.panels)} -> {', '.join(panels)}")
        family_obj.panels = panels
    if priority:
        LOG.info(f"update priority: {family_obj.priority_human} -> {priority}")
        family_obj.priority_human = priority

    context.obj["status_db"].commit()
