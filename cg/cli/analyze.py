# -*- coding: utf-8 -*-
import click

from cg.apps import tb


@click.command()
@click.option('-p', '--priority', type=click.Choice(['low', 'normal', 'high']))
@click.option('-e', '--email', help='email to send errors to')
@click.argument('family_id')
@click.pass_context
def analyze(context, priority, email, family_id):
    """Start an analysis (MIP) for a family."""
    tb_api = tb.TrailblazerAPI(context.obj)
    try:
        tb_api.start(family_id, priority=priority, email=email)
    except tb.MipStartError as error:
        click.echo(click.style(error.message, fg='red'))
