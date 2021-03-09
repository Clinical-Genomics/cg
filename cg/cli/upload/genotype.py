"""Code for uploading genotype data via CLI"""
import logging

import click
from cg.store import models

from cg.meta.upload.gt import UploadGenotypesAPI

from .utils import suggest_cases_to_upload
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.argument("family_id", required=False)
@click.pass_context
def genotypes(context, re_upload, family_id):
    """Upload genotypes from an analysis to Genotype."""

    click.echo(click.style("----------------- GENOTYPES -------------------"))
    analysis_api: MipDNAAnalysisAPI = context.obj["analysis_api"]
    if not family_id:
        suggest_cases_to_upload(context)
        context.abort()
    case_obj: models.Family = analysis_api.status_db.family(family_id)
    upload_genotypes_api = UploadGenotypesAPI(
        hk_api=analysis_api.housekeeper_api, gt_api=analysis_api.genotype_api
    )
    results = upload_genotypes_api.data(case_obj.analyses[0])

    if results:
        upload_genotypes_api.upload(results, replace=re_upload)
