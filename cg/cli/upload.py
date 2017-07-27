# -*- coding: utf-8 -*-
import click

from cg.store import Store
from cg.apps import coverage as coverage_app, gt, hk, loqus, tb, scoutapi
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.upload.observations import UploadObservationsAPI
from cg.meta.upload.scoutapi import UploadScoutAPI


@click.group(invoke_without_command=True)
@click.option('-f', '--family', 'family_id', help='Upload to all apps')
@click.pass_context
def upload(context, family_id):
    """Upload results from analyses."""
    if family_id:
        context.invoke(coverage, family_id=family_id)
        context.invoke(genotypes, family_id=family_id)
        context.invoke(observations, family_id=family_id)
        context.invoke(scout, family_id=family_id)


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
