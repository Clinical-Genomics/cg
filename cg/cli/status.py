# -*- coding: utf-8 -*-
import click

from cg.store import Store


@click.group()
@click.pass_context
def status(context):
    """View status of things."""
    context.obj['db'] = Store(context.obj['database'])


@status.command()
@click.pass_context
def analysis(context):
    """Which families are gonna be analyzed?"""
    records = context.obj['db'].families_to_analyze()
    for family_obj in records:
        click.echo(family_obj)
