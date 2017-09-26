# -*- coding: utf-8 -*-
import click

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
    """Add a new customer to the store."""
    existing = context.obj['db'].customer(internal_id)
    if existing:
        click.echo(click.style(f"customer already added: {existing.name}", fg='yellow'))
        context.abort()
    record = context.obj['db'].add_customer(internal_id=internal_id, name=name)
    context.obj['db'].add_commit(record)
    click.echo(click.style(f"customer added: {record.internal_id} ({record.id})", fg='green'))


@add.command()
@click.option('-a', '--admin', is_flag=True)
@click.option('-c', '--customer', required=True)
@click.argument('email')
@click.argument('name')
@click.pass_context
def user(context, admin, customer, email, name):
    """Add a new user."""
    customer_obj = context.obj['db'].customer(customer)
    existing = context.obj['db'].user(email)
    if existing:
        click.echo(click.style(f"user already added: {existing.name}", fg='yellow'))
        context.abort()
    record = context.obj['db'].add_user(customer_obj, email, name, admin=admin)
    context.obj['db'].add_commit(record)
    click.echo(click.style(f"user added: {record.email} ({record.id})", fg='green'))


@add.command()
@click.option('-l', '--lims', 'lims_id', help='LIMS id for the sample')
@click.option('-e', '--external', is_flag=True, help='Is sample externally sequenced?')
@click.option('-o', '--order')
@click.option('-s', '--sex', type=click.Choice(['male', 'female', 'unknown']),
              help='Sample pedigree sex', required=True)
@click.option('-a', '--application', help='Application tag', required=True)
@click.argument('customer')
@click.argument('name')
@click.pass_context
def sample(context, lims_id, external, sex, order, application, customer, name):
    """Add a sample to the store."""
    db = context.obj['db']
    customer_obj = db.customer(customer)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        context.abort()
    application_obj = db.application(application)
    if application_obj is None:
        click.echo(click.style('application not found', fg='red'))
        context.abort()
    new_record = db.add_sample(
        name=name,
        sex=sex,
        internal_id=lims_id,
        order=order,
    )
    new_record.application_version = application.versions[-1]
    new_record.customer = customer_obj
    db.add_commit(new_record)
    click.echo(click.style(f"added new sample: {new_record.name}", fg='green'))


@add.command()
@click.option('--priority', type=click.Choice(PRIORITY_OPTIONS), default='standard')
@click.option('-p', '--panel', 'panels', multiple=True, required=True, help='Default gene panels')
@click.argument('customer')
@click.argument('name')
@click.pass_context
def family(context, priority, panels, customer, name):
    """Add a family of samples."""
    db = context.obj['db']
    customer_obj = db.customer(customer)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        context.abort()

    new_family = db.add_family(customer=customer_obj, name=name, panels=panels, priority=priority)
    db.add_commit(new_family)
    click.echo(click.style(f"added new family: {new_family.internal_id}", fg='green'))


@add.command()
@click.option('-m', '--mother', help='sample if for mother of sample')
@click.option('-f', '--father', help='sample if for father of sample')
@click.option('-s', '--status', type=click.Choice(['affected', 'unaffected', 'unknown']),
              required=True)
@click.argument('family')
@click.argument('sample')
@click.pass_context
def relationship(context, mother, father, status, family, sample):
    """Relate a sample to a family."""
    db = context.obj['db']
    family_obj = db.family(family)
    sample_obj = db.sample(sample)
    mother_obj = db.sample(mother) if mother else None
    father_obj = db.sample(father) if father else None
    new_record = db.relate_sample(family_obj, sample_obj, status, mother=mother_obj,
                                  father=father_obj)
    db.add_commit(new_record)
    click.echo(f"related sample to family")
