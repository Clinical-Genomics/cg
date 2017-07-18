# -*- coding: utf-8 -*-
import click
import ruamel.yaml

from cg.store import Store


@click.command()
@click.argument('demo_file', type=click.File())
@click.pass_context
def demo(context, demo_file):
    """Setup a demo database."""
    db = Store(context.obj['database'])
    demo_data = ruamel.yaml.safe_load(demo_file)
    customers = {}
    for record_data in demo_data['customers']:
        record_obj = db.add_customer(**record_data)
        customers[record_obj.internal_id] = record_obj
        db.add(record_obj)
    for record_data in demo_data['users']:
        record_data['customer'] = customers[record_data['customer']]
        record_obj = db.add_user(**record_data)
        db.add(record_obj)
    for record_data in demo_data['applications']:
        record_obj = db.add_application(**record_data)
        db.add(record_obj)
    db.commit()
    click.echo(click.style('demo setup', fg='green'))
