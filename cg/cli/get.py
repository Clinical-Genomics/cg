import re
from typing import List

import click
from tabulate import tabulate

from cg.store import Store

SAMPLE_HEADERS = ['Sample', 'Name', 'Customer', 'Application', 'State', 'Priority',
                  'External?']
FAMILY_HEADERS = ['Family', 'Name', 'Customer', 'Priority', 'Panels', 'Action']
FLOWCELL_HEADERS = ['Flowcell', 'Type', 'Sequencer', 'Date', 'Archived?']


@click.group(invoke_without_command=True)
@click.option('-i', 'identifier', help='made a guess what type you are looking for')
@click.pass_context
def get(context: click.Context, identifier: str):
    """Get information about records in the database."""
    context.obj['status'] = Store(context.obj['database'])
    if identifier and re.match(r'^[A-Z]{3}[0-9]{4,5}[A-Z]{1}[1-9]{1,3}$', identifier):
        context.invoke(sample, sample_ids=[identifier])
    elif identifier and re.match(r'^[a-z]*$', identifier):
        # try family information
        context.invoke(family, family_ids=[identifier])
    elif identifier and re.match(r'^[HC][A-Z0-9]{8}$', identifier):
        # try flowcell information
        context.invoke(flowcell, flowcell_id=identifier)
    elif identifier:
        click.echo(click.style("can't predict identifier", fg='yellow'))


@get.command()
@click.option('--families/--no-families', default=True, help='display related families')
@click.option('-f', '--flowcells', is_flag=True, help='display related flowcells')
@click.argument('sample_ids', nargs=-1)
@click.pass_context
def sample(context: click.Context, families: bool, flowcells: bool, sample_ids: List[str]):
    """Get information about a sample."""
    for sample_id in sample_ids:
        sample_obj = context.obj['status'].sample(sample_id)
        if sample_obj is None:
            click.echo(click.style(f"sample doesn't exist: {sample_id}", fg='red'))
            continue
        row = [
            sample_obj.internal_id,
            sample_obj.name,
            sample_obj.customer.internal_id,
            sample_obj.application_version.application.tag,
            sample_obj.state,
            sample_obj.priority_human,
            'Yes' if sample_obj.application_version.application.is_external else 'No',
        ]
        click.echo(tabulate([row], headers=SAMPLE_HEADERS, tablefmt='psql'))
        if families:
            family_ids = [link_obj.family.internal_id for link_obj in sample_obj.links]
            context.invoke(family, family_ids=family_ids, samples=False)
        if flowcells:
            for flowcell_obj in sample_obj.flowcells:
                context.invoke(flowcell, flowcell_id=flowcell_obj.name, samples=False)


@get.command()
@click.option('-c', '--customer', help='internal id for customer to filter by')
@click.option('-n', '--name', is_flag=True, help='search family by name')
@click.option('--samples/--no-samples', default=True, help='display related samples')
@click.argument('family_ids', nargs=-1)
@click.pass_context
def family(context: click.Context, customer: str, name: bool, samples: bool,
           family_ids: List[str]):
    """Get information about a family."""
    if name:
        customer_obj = context.obj['status'].customer(customer)
        if customer_obj is None:
            print(click.style(f"{customer}: customer not found", fg='yellow'))
        families = context.obj['status'].families(customer=customer_obj, query=family_ids[-1])
    else:
        families = []
        for family_id in family_ids:
            family_obj = context.obj['status'].family(family_id)
            if family_obj is None:
                click.echo(click.style(f"family doesn't exist: {family_id}", fg='red'))
                context.abort()
            families.append(family_obj)

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
        if samples:
            sample_ids = [link_obj.sample.internal_id for link_obj in family_obj.links]
            context.invoke(sample, sample_ids=sample_ids, families=False)


@get.command()
@click.option('--samples/--no-samples', default=True, help='display related samples')
@click.argument('flowcell_id')
@click.pass_context
def flowcell(context: click.Context, samples: bool, flowcell_id: str):
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
    if samples:
        sample_ids = [sample_obj.internal_id for sample_obj in flowcell_obj.samples]
        if sample_ids:
            context.invoke(sample, sample_ids=sample_ids, families=False)
        else:
            click.echo(click.style('no samples found on flowcell', fg='yellow'))
