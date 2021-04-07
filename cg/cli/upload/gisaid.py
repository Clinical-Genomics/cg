"""Code for uploading genotype data via CLI"""
import logging

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

    meta_api = MetaAPI(context.obj)
    click.echo(click.style("----------------- GISAID -------------------"))

    case_obj: models.Family = meta_api.status_db.family(family_id)
    print(case_obj)
    return
    upload_gisaid_api = UploadGisaidAPI(
        hk_api=meta_api.housekeeper_api, gisaid_api=meta_api.gisaid_api
    )
    files: dict = upload_gisaid_api.files(case_obj)

    if files:
        upload_gisaid_api.upload(**files)
