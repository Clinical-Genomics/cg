# -*- coding: utf-8 -*-
import logging

import click

from cg.apps import stats, hk, lims as lims_app
from cg.meta import transfer as transfer_app
from cg.store import Store

log = logging.getLogger(__name__)


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
    stats_api = stats.StatsAPI(context.obj)
    hk_api = hk.HousekeeperAPI(context.obj)
    transfer_api = transfer_app.TransferFlowcell(context.obj['db'], stats_api, hk_api)
    new_record = transfer_api.transfer(flowcell)
    context.obj['db'].add_commit(new_record)
    click.echo(click.style(f"flowcell added: {new_record}", fg='green'))


@transfer.command()
@click.option('-s', '--status', type=click.Choice(['received', 'delivered']), default='received')
@click.pass_context
def lims(context, status):
    """Check if samples have been updated in LIMS."""
    lims_api = lims_app.LimsAPI(context.obj)
    transfer_api = transfer_app.TransferLims(context.obj['db'], lims_api)
    transfer_api.transfer_samples(status)
