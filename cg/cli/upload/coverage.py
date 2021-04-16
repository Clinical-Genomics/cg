"""Code for uploading coverage reports via CLI"""

import click
from cg.meta.upload.coverage import UploadCoverageApi
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

from .utils import suggest_cases_to_upload


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.argument("family_id", required=False)
@click.pass_obj
def coverage(context: CGConfig, re_upload, family_id):
    """Upload coverage from an analysis to Chanjo."""

    click.echo(click.style("----------------- COVERAGE --------------------"))

    status_db: Store = context.status_db

    if not family_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort

    case_obj: models.Family = status_db.family(family_id)
    upload_coverage_api = UploadCoverageApi(
        status_api=status_db,
        hk_api=context.housekeeper_api,
        chanjo_api=context.chanjo_api,
    )
    coverage_data = upload_coverage_api.data(case_obj.analyses[0])
    upload_coverage_api.upload(coverage_data, replace=re_upload)
