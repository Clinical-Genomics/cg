"""Code for uploading coverage reports via CLI"""

import click
from cg.store import models

from cg.meta.upload.coverage import UploadCoverageApi

from .utils import suggest_cases_to_upload
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.argument("family_id", required=False)
@click.pass_context
def coverage(context, re_upload, family_id):
    """Upload coverage from an analysis to Chanjo."""

    click.echo(click.style("----------------- COVERAGE --------------------"))
    analysis_api: MipDNAAnalysisAPI = context.obj["analysis_api"]
    if not family_id:
        suggest_cases_to_upload(context)
        context.abort()

    case_obj: models.Family = analysis_api.status_db.family(family_id)
    api = UploadCoverageApi(
        status_api=analysis_api.status_db,
        hk_api=analysis_api.housekeeper_api,
        chanjo_api=analysis_api.chanjo_api,
    )
    coverage_data = api.data(case_obj.analyses[0])
    api.upload(coverage_data, replace=re_upload)
