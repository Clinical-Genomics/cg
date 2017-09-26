# -*- coding: utf-8 -*-
import datetime as dt
import logging

import click

from cg.store import Store
from cg.apps import coverage as coverage_app, gt, hk, loqus, tb, scoutapi
from cg.exc import DuplicateRecordError
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.upload.observations import UploadObservationsAPI
from cg.meta.upload.scoutapi import UploadScoutAPI

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option('-f', '--family', 'family_id', help='Upload to all apps')
@click.pass_context
def upload(context, family_id):
    """Upload results from analyses."""
    context.obj['status'] = Store(context.obj['database'])
    context.obj['housekeeper_api'] = hk.HousekeeperAPI(context.obj)
    if family_id:
        family_obj = context.obj['status'].family(family_id)
        analysis_obj = family_obj.analyses[0]
        if analysis_obj.uploaded_at is not None:
            message = f"analysis already uploaded: {analysis_obj.uploaded_at.date()}"
            click.echo(click.style(message, fg='yellow'))
            context.abort()

        context.invoke(coverage, family_id=family_id)
        context.invoke(genotypes, family_id=family_id)
        context.invoke(observations, family_id=family_id)
        context.invoke(scout, family_id=family_id)

        analysis_obj.uploaded_at = dt.datetime.now()
        context.obj['status'].commit()
        click.echo(click.style(f"{family_id}: analysis uploaded!", fg='green'))


@upload.command()
@click.argument('family_id')
@click.pass_context
def coverage(context, family_id):
    """Upload coverage from an analysis to Chanjo."""
    chanjo_api = coverage_app.ChanjoAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadCoverageApi(context.obj['status'], context.obj['housekeeper_api'], chanjo_api)
    coverage_data = api.data(family_obj.analyses[0])
    api.upload(coverage_data)


@upload.command()
@click.argument('family_id')
@click.pass_context
def genotypes(context, family_id):
    """Upload genotypes from an analysis to Genotype."""
    tb_api = tb.TrailblazerAPI(context.obj)
    gt_api = gt.GenotypeAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadGenotypesAPI(context.obj['status'], context.obj['housekeeper_api'], tb_api, gt_api)
    results = api.data(family_obj.analyses[0])
    api.upload(results)


@upload.command()
@click.argument('family_id')
@click.pass_context
def observations(context, family_id):
    """Upload observations from an analysis to LoqusDB."""
    loqus_api = loqus.LoqusdbAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadObservationsAPI(context.obj['status'], context.obj['housekeeper_api'], loqus_api)
    try:
        api.process(family_obj.analyses[0])
        click.echo(click.style(f"{family_id}: observations uploaded!", fg='green'))
    except DuplicateRecordError as error:
        LOG.info(f"skipping observations upload: {error.message}")


@upload.command()
@click.argument('family_id')
@click.pass_context
def scout(context, family_id):
    """Upload variants from analysis to Scout."""
    scout_api = scoutapi.ScoutAPI(context.obj)
    family_obj = context.obj['status'].family(family_id)
    api = UploadScoutAPI(context.obj['status'], context.obj['housekeeper_api'], scout_api)
    results = api.data(family_obj.analyses[0])
    scout_api.upload(results)


@upload.command()
@click.pass_context
def auto(context):
    """Upload all completed analyses."""
    for analysis_obj in context.obj['status'].analyses_to_upload():
        LOG.info(f"uploading family: {analysis_obj.family.internal_id}")
        context.invoke(upload, family_id=analysis_obj.family.internal_id)
