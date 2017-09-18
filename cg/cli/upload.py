# -*- coding: utf-8 -*-
import datetime as dt
import click
import logging

from cg.store import Store
from cg.apps import coverage as coverage_app, gt, hk, loqus, tb, scoutapi
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
    if family_id:
        status_api = Store(context.obj['database'])
        family_obj = status_api.family(family_id)
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
        status_api.commit()
        click.echo(click.style(f"{family_id}: analysis uploaded!", fg='green'))


@upload.command()
@click.argument('family_id')
@click.pass_context
def coverage(context, family_id):
    """Upload coverage from an analysis to Chanjo."""
    status_api = Store(context.obj['database'])
    hk_api = hk.HousekeeperAPI(context.obj)
    chanjo_api = coverage_app.ChanjoAPI(context.obj)
    family_obj = status_api.family(family_id)
    api = UploadCoverageApi(status_api, hk_api, chanjo_api)
    coverage_data = api.data(family_obj.analyses[0])
    api.upload(coverage_data)


@upload.command()
@click.argument('family_id')
@click.pass_context
def genotypes(context, family_id):
    """Upload genotypes from an analysis to Genotype."""
    status_api = Store(context.obj['database'])
    hk_api = hk.HousekeeperAPI(context.obj)
    tb_api = tb.TrailblazerAPI(context.obj)
    gt_api = gt.GenotypeAPI(context.obj)
    family_obj = status_api.family(family_id)
    api = UploadGenotypesAPI(status_api, hk_api, tb_api, gt_api)
    results = api.data(family_obj.analyses[0])
    api.upload(results)


@upload.command()
@click.argument('family_id')
@click.pass_context
def observations(context, family_id):
    """Upload observations from an analysis to LoqusDB."""
    status_api = Store(context.obj['database'])
    hk_api = hk.HousekeeperAPI(context.obj)
    loqus_api = loqus.LoqusdbAPI(context.obj)
    family_obj = status_api.family(family_id)
    api = UploadObservationsAPI(status_api, hk_api, loqus_api)
    results = api.data(family_obj.analyses[0])
    api.upload(results)


@upload.command()
@click.argument('family_id')
@click.pass_context
def scout(context, family_id):
    """Upload variants from analysis to Scout."""
    status_api = Store(context.obj['database'])
    hk_api = hk.HousekeeperAPI(context.obj)
    scout_api = scoutapi.ScoutAPI(context.obj)
    family_obj = status_api.family(family_id)
    api = UploadScoutAPI(status_api, hk_api, scout_api)
    results = api.data(family_obj.analyses[0])
    scout_api.upload(results)


@upload.command()
@click.pass_context
def auto(context):
    """Upload all completed analyses."""
    for analysis_obj in context.obj['db'].analyses_to_upload():
        LOG.info(f"uploading family: {analysis_obj.family.internal_id}")
        context.invoke(upload, family_id=analysis_obj.family.internal_id)
