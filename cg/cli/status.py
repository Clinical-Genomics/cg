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


@status.command()
@click.option('-s', '--skip', default=0, help='skip initial families')
@click.pass_context
def families(context, skip):
    """View status of families."""
    records = context.obj['db'].families().offset(skip).limit(30)
    for family_obj in records:
        color = 'red' if family_obj.priority > 1 else 'blue'
        message = f"{family_obj.internal_id} ({family_obj.priority})"
        if family_obj.analyses:
            message += f" {family_obj.analyses[0].analyzed_at.date()}"
            color = 'green'
        if family_obj.analyze:
            message += ' [ANALYZE]'
            color = 'orange'
        click.echo(click.style(message, fg=color))
