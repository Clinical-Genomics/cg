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
@click.option('-s', '--skip', default=0, help='skip initial records')
@click.pass_context
def samples(context, skip):
    """View status of samples."""
    records = context.obj['db'].samples().offset(skip).limit(30)
    for record in records:
        message = f"{record.internal_id} ({record.customer.internal_id})"
        if record.sequenced_at:
            color = 'green'
            message += f" [SEQUENCED: {record.sequenced_at.date()}]"
        elif record.received_at and record.reads:
            color = 'orange'
            message += f" [READS: {record.reads}]"
        elif record.received_at:
            color = 'blue'
            message += f" [RECEIVED: {record.received_at.date()}]"
        else:
            color = 'grey'
            message += ' [NOT RECEIVED]'
        click.echo(click.style(message, fg=color))


@status.command()
@click.option('-s', '--skip', default=0, help='skip initial records')
@click.pass_context
def families(context, skip):
    """View status of families."""
    records = context.obj['db'].families().offset(skip).limit(30)
    for family_obj in records:
        color = 'red' if family_obj.priority > 1 else 'blue'
        message = f"{family_obj.internal_id} ({family_obj.priority})"
        if family_obj.analyses:
            message += f" {family_obj.analyses[0].completed_at.date()}"
            color = 'green'
        if family_obj.analyze:
            message += ' [ANALYZE]'
            color = 'orange'
        click.echo(click.style(message, fg=color))
