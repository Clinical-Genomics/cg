# -*- coding: utf-8 -*-
import click

from cg.apps.stats import StatsAPI
from cg.apps.housekeeper import HousekeeperAPI
from cg.meta import transfer as transfer_app
from cg.store import Store


@click.group()
@click.pass_context
def transfer(context):
    """Transfer results to the status interface."""
    context.obj['db'] = Store(context.obj['database'])


@transfer.command()
@click.argument('flowcell')
@click.pass_context
def flowcell(context, flowcell):
    """Populate results from a flowcell."""
    stats_api = StatsAPI(context.obj)
    hk_api = HousekeeperAPI(context.obj)
    transfer_api = transfer_app.TransferFlowcell(context.obj['db'], stats_api, hk_api)
    new_record = transfer_api.transfer(flowcell)
    context.obj['db'].add_commit(new_record)
    click.echo(click.style(f"flowcell added: {new_record}", fg='green'))
