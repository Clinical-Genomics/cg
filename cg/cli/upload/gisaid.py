"""Code for uploading genotype data via CLI"""
import logging
import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.upload.gisaid import GisaidAPI
from cg.meta.upload.gisaid.models import UpploadFiles
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("family_id", required=True)
@click.pass_context
def gisaid(context: CGConfig, family_id):
    """Upload mutant analysis data to GISAID."""

    status_db: Store = context.status_db
    hk: HousekeeperAPI = context.housekeeper_api
    gisaid_api: GisaidAPI(context, status_db, hk)
    LOG.info("----------------- GISAID -------------------")

    case_object: Family = status_db.family(family_id)
    if not case_object:
        LOG.warning("Could not family: %s in status-db", family_id)
        raise click.Abort
    gsaid_samples = gisaid_api.get_gsaid_samples(family_id=family_id)
    files: UpploadFiles = UpploadFiles(
        csv_file=gisaid_api.build_gisaid_csv(gsaid_samples=gsaid_samples),
        fasta_file=gisaid_api.build_gisaid_fasta(gsaid_samples=gsaid_samples),
    )
    if files:
        gisaid_api.upload(**dict(files))
