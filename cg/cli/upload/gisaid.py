"""Code for uploading genotype data via CLI"""
import logging

import click

from cg.meta.upload.gisaid import GisaidAPI
from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


@click.command()
@click.argument("case_id", required=True)
@click.pass_obj
def gisaid(context: CGConfig, case_id: str):
    """Upload mutant analysis data to GISAID."""

    LOG.info("----------------- GISAID UPLOAD -------------------")

    gisaid_api = GisaidAPI(config=context)

    gisaid_api.upload(case_id=case_id)
    LOG.info("Upload to GISAID successful")
