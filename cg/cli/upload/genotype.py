"""Code for uploading genotype data via CLI"""
import logging

import click
from cg.meta.upload.gt import UploadGenotypesAPI

from .utils import suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.argument("family_id", required=False)
@click.pass_context
def genotypes(context, re_upload, family_id):
    """Upload genotypes from an analysis to Genotype."""

    click.echo(click.style("----------------- GENOTYPES -------------------"))

    if not family_id:
        suggest_cases_to_upload(context)
        context.abort()

    gt_api = context.obj["genotype_api"]
    hk_api = context.obj["housekeeper_api"]
    status_api = context.obj["status_db"]
    case_obj = status_api.family(family_id)
    upload_genotypes_api = UploadGenotypesAPI(hk_api=hk_api, gt_api=gt_api)
    results = upload_genotypes_api.data(case_obj.analyses[0])

    if results:
        upload_genotypes_api.upload(results, replace=re_upload)
