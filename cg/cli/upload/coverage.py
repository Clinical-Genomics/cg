"""Code for uploading coverage reports via CLI"""

import rich_click as click

from cg.meta.upload.coverage import UploadCoverageApi
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store

from .utils import suggest_cases_to_upload


@click.command("coverage")
@click.argument("family_id", required=False)
@click.pass_obj
def upload_coverage(context: CGConfig, family_id):
    """Upload coverage from an analysis to Chanjo."""

    click.echo(click.style("----------------- COVERAGE --------------------"))

    status_db: Store = context.status_db

    if not family_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort

    case: Case = status_db.get_case_by_internal_id(internal_id=family_id)
    upload_coverage_api = UploadCoverageApi(
        status_api=status_db,
        hk_api=context.housekeeper_api,
        chanjo_api=context.chanjo_api,
    )
    coverage_data = upload_coverage_api.data(case.latest_completed_analysis)
    upload_coverage_api.upload(coverage_data)
