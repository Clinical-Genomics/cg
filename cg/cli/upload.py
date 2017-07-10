# -*- coding: utf-8 -*-
import click

from cg.store import Store
from cg.apps import coverage as coverage_app, gt, hk, tb
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.upload.gt import UploadGenotypesAPI


@click.group()
def upload():
    """Upload results from analyses."""
    pass


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
