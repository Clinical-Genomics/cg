# -*- coding: utf-8 -*-
import logging

import click

from cg.apps import stats, hk, lims
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
@click.argument('lims_id', required=False)
@click.pass_context
def delivered(context, lims_id):
    """Check if samples ready to deliver have been delivered in LIMS."""
    lims_api = lims.LimsAPI(context)
    if lims_id:
        sample_obj = context.obj['db'].sample(lims_id)
        if sample_obj is None:
            click.echo(click.style(f"sample not found", fg='red'))
            context.abort()
        samples = [sample_obj]
    else:
        samples = context.obj['db'].samples_to_deliver()

    for sample_obj in samples:
        log.debug(f"looking up delivery date for: {sample_obj.internal_id}")
        delivered_date = lims_api.get_delivery(sample_obj.internal_id)
        if delivered_date:
            sample_obj.delivered_at = delivered_date
            context.obj['db'].commit()
            click.echo(click.style(f"sample delivered: {sample_obj.internal_id}", fg='green'))
