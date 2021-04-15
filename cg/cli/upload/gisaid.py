"""Code for uploading genotype data via CLI"""
import logging
import click
from cg.apps.gisaid.gisaid import GisaidAPI
from cg.apps.gisaid.models import UpploadFiles
from cg.store import models, Store
from cg.store.models import Family

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("family_id", required=True)
@click.pass_context
def gisaid(context, family_id):
    """Upload mutant analysis data to GISAID."""

    gisaid_api: GisaidAPI = GisaidAPI(context.obj)
    status_db: Store = gisaid_api.status_db
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
