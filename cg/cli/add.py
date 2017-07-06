# -*- coding: utf-8 -*-
import click

from cg.apps import lims
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
@click.argument('customer')
@click.argument('family_name')
@click.pass_context
def family(context, customer, family_name):
    """Add a family of samples from LIMS."""
    db = context.obj['db']
    lims_api = lims.ClinicalLims(context.obj)
    customer_obj = db.customer(customer)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        context.abort()
    family_data = lims_api.family(customer, family_name)
    existing = db.find_family(customer_obj, family_name)
    if existing:
        click.echo(click.style(f"family already added: {existing.internal_id}", fg='yellow'))
        context.abort()
    family_obj = db.add_family(customer_obj, family_name, priority=family_data['priority'])
    db.add(family_obj)
    click.echo(click.style(f"family added: {family_obj.internal_id}", fg='green'))
    for sample_data in family_data['samples']:
        sample_obj = db.add_sample(customer_obj, family_obj, id=sample_data['id'],
                                   name=sample_data['name'], received=sample_data['received'])
        db.add(sample_obj)
        click.echo(click.style(f"sample added: {sample_obj.internal_id}", fg='green'))
    db.commit()
