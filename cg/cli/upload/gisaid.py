"""Code for uploading genotype data via CLI"""
import logging
from typing import List

import click

from cg.meta.upload.gisaid import GisaidAPI
from cg.meta.upload.gisaid.models import UpploadFiles, GisaidSample
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("family_id", required=True)
@click.pass_obj
def gisaid(context: CGConfig, family_id: str):
    """Upload mutant analysis data to GISAID."""

    LOG.info("----------------- GISAID -------------------")

    gisaid_api = GisaidAPI(config=context)
    gsaid_samples: List[GisaidSample] = gisaid_api.get_gsaid_samples(family_id=family_id)
    files: UpploadFiles = UpploadFiles(
        csv_file=gisaid_api.build_gisaid_csv(
            gsaid_samples=gsaid_samples, file_name=f"{family_id}.csv"
        ),
        fasta_file=gisaid_api.build_gisaid_fasta(
            gsaid_samples=gsaid_samples, file_name=f"{family_id}.fasta"
        ),
    )
    if files:
        gisaid_api.upload(**dict(files))
        files.csv_file.unlink()
        files.fasta_file.unlink()
