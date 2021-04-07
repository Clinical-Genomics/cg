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

    meta_api = MetaAPI(context.obj)
    click.echo(click.style("----------------- GISAID -------------------"))

    samples: List[models.Sample] = meta_api.status_db.samples(family_id)
    return
    upload_gisaid_api = UploadGisaidAPI(
        hk_api=meta_api.housekeeper_api, gisaid_api=meta_api.gisaid_api
    )
    files: dict = upload_gisaid_api.files(samples=samples, family_id=family_id)

    if files:
        upload_gisaid_api.upload(**files)
