"""Set family attributes in the status database"""


import click
from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS


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

    family_obj = context.obj["status"].family(family_id)
    if family_obj is None:
        click.echo(click.style(f"Can't find family {family_id}", fg="red"))
        context.abort()
    if not any([action, panels, priority, customer_id]):
        click.echo(click.style(f"Nothing to change", fg="yellow"))
        context.abort()
    if action:
        click.echo(
            click.style(f"Update action: {family_obj.action or 'NA'} -> {action}", fg="green")
        )
        family_obj.action = action
    if customer_id:
        customer_obj = context.obj["status"].customer(customer_id)
        if customer_obj is None:
            click.echo(click.style(f"unknown customer: {customer_id}", fg="red"))
            context.abort()
        click.echo(
            click.style(
                f"Update customer: {family_obj.customer.internal_id} -> {customer_id}", fg="green"
            )
        )
        family_obj.customer = customer_obj
    if panels:
        for panel_id in panels:
            panel_obj = context.obj["status"].panel(panel_id)
            if panel_obj is None:
                click.echo(click.style(f"unknown gene panel: {panel_id}", fg="red"))
                context.abort()
        message = f"update panels: {', '.join(family_obj.panels)} -> {', '.join(panels)}"
        click.echo(click.style(message, fg="green"))
        family_obj.panels = panels
    if priority:
        message = f"update priority: {family_obj.priority_human} -> {priority}"
        click.echo(click.style(message, fg="green"))
        family_obj.priority_human = priority

    context.obj["status"].commit()
