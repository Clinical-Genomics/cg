import re

import click
from tabulate import tabulate

from cg.store import Store

SAMPLE_HEADERS = ['Sample', 'Name', 'Customer', 'Application', 'State', 'Priority', 'External?']
FAMILY_HEADERS = ['Family', 'Name', 'Customer', 'Priority', 'Panels', 'Action']
FLOWCELL_HEADERS = ['Flowcell', 'Type', 'Sequencer', 'Date', 'Archived?']


@click.group(invoke_without_command=True)
@click.option('-i', 'identifier', help='made a guess what type you are looking for')
@click.pass_context
def get(context, identifier):
    """Get information about records in the database."""
    context.obj['status'] = Store(context.obj['database'])
    if identifier and re.match(r'^[A-Z]{3}[0-9]{4,5}[A-Z]{1}[1-9]{1,3}$', identifier):
        context.invoke(sample, sample_ids=[identifier])
    elif identifier and re.match(r'^[a-z]*$', identifier):
        # try family information
        context.invoke(family, family_id=identifier)
    elif identifier and re.match(r'^[HC][A-Z0-9]{8}$', identifier):
        # try flowcell information
        context.invoke(flowcell, flowcell_id=identifier)
    elif identifier:
        click.echo(click.style("can't predict identifier", fg='yellow'))


@get.command()
@click.argument('sample_ids', nargs=-1)
@click.pass_context
def sample(context, sample_ids):
    """Get information about a sample."""
    table = []
    for sample_id in sample_ids:
        sample_obj = context.obj['status'].sample(sample_id)
        if sample_obj is None:
            click.echo(click.style(f"sample doesn't exist: {sample_id}", fg='red'))
            continue
        table.append([
            sample_obj.internal_id,
            sample_obj.name,
            sample_obj.customer.internal_id,
            sample_obj.application_version.application.tag,
            sample_obj.state,
            sample_obj.priority_human,
            'Yes' if sample_obj.application_version.application.is_external else 'No',
        ])
    click.echo(tabulate(table, headers=SAMPLE_HEADERS, tablefmt='psql'))


@get.command()
@click.option('-c', '--customer', help='internal id for customer to filter by')
@click.option('-n', '--name', is_flag=True, help='search family by name')
@click.argument('family_id')
@click.pass_context
def family(context, customer, name, family_id):
    """Get information about a family."""
    if name:
        customer_obj = context.obj['status'].customer(customer)
        if customer_obj is None:
            print(click.style(f"{customer}: customer not found", fg='yellow'))
        families = context.obj['status'].families(customer=customer_obj, query=family_id)
    else:
        family_obj = context.obj['status'].family(family_id)
        if family_obj is None:
            click.echo(click.style(f"family doesn't exist: {family_id}", fg='red'))
            context.abort()
        families = [family_obj]

    for family_obj in families:
        row = [
            family_obj.internal_id,
            family_obj.name,
            family_obj.customer.internal_id,
            family_obj.priority_human,
            ', '.join(family_obj.panels),
            family_obj.action or 'NA',
        ]
        click.echo(tabulate([row], headers=FAMILY_HEADERS, tablefmt='psql'))
        sample_ids = [link_obj.sample.internal_id for link_obj in family_obj.links]
        context.invoke(sample, sample_ids=sample_ids)


@get.command()
@click.argument('flowcell_id')
@click.pass_context
def flowcell(context, flowcell_id):
    """Get information about a flowcell and the samples on it."""
    flowcell_obj = context.obj['status'].flowcell(flowcell_id)
    if flowcell_obj is None:
        click.echo(click.style(f"flowcell doesn't exist: {flowcell_id}", fg='red'))
        context.abort()
    row = [
        flowcell_obj.name,
        flowcell_obj.sequencer_type,
        flowcell_obj.sequencer_name,
        flowcell_obj.sequenced_at.date(),
        flowcell_obj.archived_at.date() if flowcell_obj.archived_at else 'No',
    ]
    click.echo(tabulate([row], headers=FLOWCELL_HEADERS, tablefmt='psql'))
    sample_ids = [sample_obj.internal_id for sample_obj in flowcell_obj.samples]
    if sample_ids:
        context.invoke(sample, sample_ids=sample_ids)
    else:
        click.echo(click.style('no samples found on flowcell', fg='yellow'))
