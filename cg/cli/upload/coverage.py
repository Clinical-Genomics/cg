"""Code for uploading coverage reports via CLI"""

from typing import cast

import rich_click as click

from cg.apps.coverage.api import ChanjoAPI
from cg.meta.upload.coverage import UploadCoverageApi
from cg.models.cg_config import CGConfig, ChanjoConfig
from cg.store.models import Case
from cg.store.store import Store

from .utils import suggest_cases_to_upload


@click.command("coverage")
@click.argument("family_id", required=False)
@click.option(
    "--genome-version",
    type=click.Choice(["hg19", "hg38"]),
    default="hg19",
    help="Which chanjo instance to upload to",
)
@click.pass_obj
def upload_coverage(context: CGConfig, family_id, genome_version: str):
    """Upload coverage from an analysis to Chanjo."""

    click.echo(click.style("----------------- COVERAGE --------------------"))

    status_db: Store = context.status_db

    if not family_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort

    case: Case = status_db.get_case_by_internal_id(internal_id=family_id)
    chanjo_config = cast(
        ChanjoConfig, context.chanjo_38 if genome_version == "hg38" else context.chanjo
    )
    chanjo_api = ChanjoAPI(config=chanjo_config)
    upload_coverage_api = UploadCoverageApi(
        status_api=status_db,
        hk_api=context.housekeeper_api,
        chanjo_api=chanjo_api,
    )
    coverage_data = upload_coverage_api.data(case.latest_completed_analysis)
    upload_coverage_api.upload(coverage_data)
