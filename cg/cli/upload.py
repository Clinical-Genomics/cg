# -*- coding: utf-8 -*-
import click

from cg.store import Store
from cg.apps import hk, coverage as coverage_app
from cg.apps.upload.coverage import UploadCoverageApi


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
