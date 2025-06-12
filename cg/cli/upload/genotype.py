"""Code for uploading genotype data via CLI"""

import logging

import rich_click as click

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis
from cg.store.store import Store

from .utils import suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command("genotypes")
@click.option(
    "-r",
    "--re-upload",
    is_flag=True,
    help="re-upload existing analysis",
)
@click.argument("family_id", required=False)
@click.pass_obj
def upload_genotypes(context: CGConfig, re_upload: bool, family_id: str | None):
    """Upload genotypes from an analysis to Genotype."""

    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    genotype_api: GenotypeAPI = context.genotype_api
    click.echo(click.style("----------------- GENOTYPES -------------------"))

    if not family_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort
    analysis: Analysis = status_db.get_latest_completed_analysis_for_case(family_id)
    upload_genotypes_api = UploadGenotypesAPI(hk_api=housekeeper_api, gt_api=genotype_api)
    results: dict = upload_genotypes_api.get_genotype_data(analysis)

    if not results:
        LOG.warning("Could not find any results to upload")
        return
    upload_genotypes_api.upload(results, replace=re_upload)
