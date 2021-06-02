"""Code for uploading genotype data via CLI"""
import logging

import click

from cg.meta.upload.gisaid import GisaidAPI
from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


@click.command()
@click.argument("family_id", required=True)
@click.pass_obj
def gisaid(context: CGConfig, family_id: str):
    """Upload mutant analysis data to GISAID."""

    LOG.info("----------------- GISAID UPLOAD-------------------")

    gisaid_api = GisaidAPI(config=context)
    try:
        gisaid_api.upload(family_id=family_id)
    except:
        LOG.info("send an email")
