# -*- coding: utf-8 -*-
import click

from cg.constants import PRIORITY_OPTIONS
from cg.store import Store


@click.group()
@click.pass_context
def add(context):
    """Add new things to the database."""
    context.obj['db'] = Store(context.obj['database'])


@add.command()
@click.argument('internal_id')
@click.argument('name')
@click.pass_context
def customer(context, internal_id: str, name: str):
    """Add a new customer with a unique INTERNAL_ID and NAME."""
    existing = context.obj['db'].customer(internal_id)
    if existing:
        click.echo(click.style(f"customer already added: {existing.name}", fg='yellow'))
        context.abort()
    new_customer = context.obj['db'].add_customer(internal_id=internal_id, name=name)
    context.obj['db'].add_commit(new_customer)
    message = f"customer added: {new_customer.internal_id} ({new_customer.id})"
    click.echo(click.style(message, fg='green'))


@add.command()
@click.option('-a', '--admin', is_flag=True, help='make the user an admin')
@click.option('-c', '--customer', 'customer_id', required=True,
              help='internal ID for the customer of the user')
@click.argument('email')
@click.argument('name')
@click.pass_context
def user(context, admin, customer_id, email, name):
    """Add a new user with an EMAIL (login) and a NAME (full)."""
    customer_obj = context.obj['db'].customer(customer_id)
    existing = context.obj['db'].user(email)
    if existing:
        click.echo(click.style(f"user already added: {existing.name}", fg='yellow'))
        context.abort()
    new_user = context.obj['db'].add_user(customer_obj, email, name, admin=admin)
    context.obj['db'].add_commit(new_user)
    click.echo(click.style(f"user added: {new_user.email} ({new_user.id})", fg='green'))


@add.command()
@click.option('-l', '--lims', 'lims_id', help='LIMS id for the sample')
@click.option('-d', '--downsampled', type=int, help='how many reads is the sample downsampled to?')
@click.option('-o', '--order', help='name of the order the sample belongs to')
@click.option('-s', '--sex', type=click.Choice(['male', 'female', 'unknown']), required=True,
              help='sample pedigree sex')
@click.option('-a', '--application', required=True, help='application tag name')
@click.option('-p', '--priority', type=click.Choice(PRIORITY_OPTIONS), default='standard',
              help='set the priority for the samples')
@click.argument('customer_id')
@click.argument('name')
@click.pass_context
def sample(context, lims_id, downsampled, sex, order, application, priority, customer_id, name):
    """Add a sample for CUSTOMER_ID with a NAME (display)."""
    status = context.obj['db']
    customer_obj = status.customer(customer_id)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        context.abort()
    application_obj = status.application(application)
    if application_obj is None:
        click.echo(click.style('application not found', fg='red'))
        context.abort()
    new_record = status.add_sample(
        name=name,
        sex=sex,
        internal_id=lims_id,
        order=order,
        downsampled_to=downsampled,
        priority=priority,
    )
    new_record.application_version = application_obj.versions[-1]
    new_record.customer = customer_obj
    status.add_commit(new_record)
    click.echo(click.style(f"added new sample: {new_record.internal_id}", fg='green'))


@add.command()
@click.option('--priority', type=click.Choice(PRIORITY_OPTIONS), default='standard',
              help='analysis priority')
@click.option('-p', '--panel', 'panels', multiple=True, required=True, help='default gene panels')
@click.argument('customer_id')
@click.argument('name')
@click.pass_context
def family(context, priority, panels, customer_id, name):
    """Add a family to CUSTOMER_ID with a NAME."""
    status = context.obj['db']
    customer_obj = status.customer(customer_id)
    if customer_obj is None:
        click.echo(click.style('customer not found', fg='red'))
        context.abort()

    for panel_id in panels:
        panel_obj = status.panel(panel_id)
        if panel_obj is None:
            print(click.style(f"{panel_id}: panel not found", fg='red'))
            context.abort()

    new_family = status.add_family(
        name=name,
        panels=panels,
        priority=priority,
    )
    new_family.customer = customer_obj
    status.add_commit(new_family)
    click.echo(click.style(f"added new family: {new_family.internal_id}", fg='green'))


@add.command()
@click.option('-m', '--mother', help='sample ID for mother of sample')
@click.option('-f', '--father', help='sample ID for father of sample')
@click.option('-s', '--status', type=click.Choice(['affected', 'unaffected', 'unknown']),
              required=True)
@click.argument('family_id')
@click.argument('sample_id')
@click.pass_context
def relationship(context, mother, father, status, family_id, sample_id):
    """Create a link between a FAMILY_ID and a SAMPLE_ID."""
    status_db = context.obj['db']
    family_obj = status_db.family(family_id)
    sample_obj = status_db.sample(sample_id)
    mother_obj = status_db.sample(mother) if mother else None
    father_obj = status_db.sample(father) if father else None
    new_record = status_db.relate_sample(family_obj, sample_obj, status, mother=mother_obj,
                                         father=father_obj)
    status_db.add_commit(new_record)
    click.echo(f"related sample to family")
