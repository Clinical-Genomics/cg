"""Code for uploading genotype data via CLI"""
import logging
from typing import Optional

import click
from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

from .utils import suggest_cases_to_upload

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-r", "--re-upload", is_flag=True, help="re-upload existing analysis")
@click.argument("family_id", required=False)
@click.pass_obj
def genotypes(context: CGConfig, re_upload: bool, family_id: Optional[str]):
    """Upload genotypes from an analysis to Genotype."""

    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    genotype_api: GenotypeAPI = context.genotype_api

    click.echo(click.style("----------------- GENOTYPES -------------------"))

    if not family_id:
        suggest_cases_to_upload(status_db=status_db)
        raise click.Abort
    case_obj: models.Family = status_db.family(family_id)
    upload_genotypes_api = UploadGenotypesAPI(hk_api=housekeeper_api, gt_api=genotype_api)
    results: dict = upload_genotypes_api.data(case_obj.analyses[0])

    if not results:
        LOG.warning("Could not find any results to upload")
        return
    upload_genotypes_api.upload(results, replace=re_upload)
