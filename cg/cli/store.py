# -*- coding: utf-8 -*-
import datetime as dt
import logging
from pathlib import Path

import click

from cg.apps import hk, tb
from cg.store import Store
from cg.meta.analysis import AnalysisAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def store(context):
    """Store results from MIP in housekeeper."""
    context.obj['db'] = Store(context.obj['database'])
    context.obj['tb_api'] = tb.TrailblazerAPI(context.obj)
    context.obj['hk_api'] = hk.HousekeeperAPI(context.obj)



@store.command()
@click.argument('config_stream', type=click.File('r'))
@click.pass_context
def analysis(context, config_stream):
    """Store a finished analysis in Housekeeper."""
    context.obj['api'] = AnalysisAPI(
        db=context.obj['db'],
        hk_api=context.obj['hk_api'],
        tb_api=context.obj['tb_api'],
        scout_api=None,
        lims_api=None,
        deliver_api=None,
        fastq_handler=None
    ).store_analysis(config_stream)
    click.echo(click.style('included files in Housekeeper', fg='green'))


@store.command()
@click.pass_context
def completed(context):
    """Store all completed analyses."""
    hk_api = context.obj['hk_api']
    for analysis_obj in context.obj['tb_api'].analyses(status='completed', deleted=False):
        existing_record = hk_api.version(analysis_obj.family, analysis_obj.started_at)
        if existing_record:
            LOG.debug(f"analysis stored: {analysis_obj.family} - {analysis_obj.started_at}")
            continue
        click.echo(click.style(f"storing family: {analysis_obj.family}", fg='blue'))
        with Path(analysis_obj.config_path).open() as config_stream:
            context.invoke(analysis, config_stream=config_stream)
