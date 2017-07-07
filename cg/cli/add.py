# -*- coding: utf-8 -*-
import click

from cg.apps import lims
from cg.constants import PRIORITY_OPTIONS
from cg.store import Store


@click.group()
@click.pass_context
def add(context):
    """Add things to the store."""
    context.obj['db'] = Store(context.obj['database'])


@add.command()
@click.argument('internal_id')
@click.argument('name')
@click.pass_context
def customer(context, internal_id, name):
    """Start an analysis (MIP) for a family."""
    existing = context.obj['db'].customer(internal_id)
    if existing:
        click.echo(click.style(f"customer already added: {existing.name}", fg='yellow'))
        context.abort()
    record = context.obj['db'].add_customer(internal_id=internal_id, name=name)
    context.obj['db'].add_commit(record)
    click.echo(click.style(f"customer added: {record.internal_id} ({record.id})", fg='green'))


@add.command()
@click.option('-l', '--lims', 'lims_id', help='LIMS id for the sample')
@click.option('-e', '--external', is_flag=True, help='Is sample externally sequenced?')
@click.argument('customer')
@click.argument('name')
@click.pass_context
def sample(context, lims_id, external, customer, name):
    """Add a sample to the store."""
    db = context.obj['db']
    customer_obj = db.customer(customer)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        context.abort()
    new_record = db.add_sample(
        customer=customer_obj,
        name=name,
        lims_id=lims_id,
        external=external,
    )
    db.add_commit(new_record)
    click.echo(click.style(f"added new family: {new_record.name}"), fg='green')


@add.command()
@click.option('--priority', type=click.Choice(PRIORITY_OPTIONS), default='standard')
@click.option('-p', '--panels', nargs=-1, required=True, help='Default gene panels')
@click.option('-s', '--samples', nargs=-1, required=True, help='Samples in the family')
@click.argument('customer')
@click.argument('name')
@click.pass_context
def family(context, priority, panels, samples, customer, name):
    """Add a family of samples."""
    db = context.obj['db']
    customer_obj = db.customer(customer)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        context.abort()

    new_family = db.add_family(
        customer=customer_obj,
        name=name,
        panels=panels,
        samples=[db.sample(sample) for sample in samples],
        priority=priority,
    )
    db.add_commit(new_family)
    click.echo(click.style(f"added new family: {new_family.internal_id}"), fg='green')


def add_family_auto(db, config, customer, family_name):
    """Auto-add family based on information in LIMS."""
    lims_api = lims.ClinicalLims(config)
    customer_obj = db.customer(customer)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        return
    family_data = lims_api.family(customer, family_name)
    existing = db.find_family(customer_obj, family_name)
    if existing:
        click.echo(click.style(f"family already added: {existing.internal_id}", fg='yellow'))
        return
    family_obj = db.add_family(customer_obj, family_name, priority=family_data['priority'])
    db.add(family_obj)
    click.echo(click.style(f"family added: {family_obj.internal_id}", fg='green'))
    for sample_data in family_data['samples']:
        sample_obj = db.add_sample(customer_obj, family_obj, id=sample_data['id'],
                                   name=sample_data['name'], received=sample_data['received'])
        db.add(sample_obj)
        click.echo(click.style(f"sample added: {sample_obj.internal_id}", fg='green'))
    db.commit()
