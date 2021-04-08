"""Code for uploading genotype data via CLI"""
import logging
from typing import List

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
    ticket_number: str = case_object.name
    samples: List[models.Sample] = status_db.Sample.query.filter_by(
        ticket_number=ticket_number
    ).all()

    files: UpploadFiles = gisaid_api.files(samples=samples, family_id=family_id)
    if files:
        gisaid_api.upload(**dict(files))
