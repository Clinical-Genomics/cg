"""Code for uploading genotype data via CLI"""
import logging
from typing import List

import click
from cg.store import models

from cg.meta.upload.gisaid import UploadGisaidAPI

from .utils import suggest_cases_to_upload
from cg.meta.meta import MetaAPI

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("family_id", required=True)
@click.pass_context
def gisaid(context, family_id):
    """Upload mutant analysis data to GISAID."""

    print(context.obj)
    #if not context.obj.get("analysis_api"):
    #    context.obj["analysis_api"] = MetaAPI(context.obj)
    #analysis_api = context.obj["analysis_api"]

    meta_api=MetaAPI(context.obj)
    click.echo(click.style("----------------- GISAID -------------------"))
    return
    if not family_id:
#        suggest_cases_to_upload(context)
        context.abort()
    case_obj: models.Family = analysis_api.status_db.family(family_id)
    upload_gisaid_api = UploadGisaidAPI(
        hk_api=meta_api.housekeeper_api, gisaid_api=meta_api.gisaid_api
    )
    results = upload_gisaid_api.data(case_obj)

    if results:
        upload_gisaid_api.upload(results)
