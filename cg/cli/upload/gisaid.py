"""Code for uploading genotype data via CLI"""
import logging
from typing import List, Dict

import click

from cg.meta.upload.gisaid import GisaidAPI
from cg.meta.upload.gisaid.models import UpploadFiles, GisaidSample, CompletionFiles
from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


@click.group()
def gisaid():
    """Upload NIPT result files"""
    pass


@gisaid.command()
@click.argument("family_id", required=True)
@click.pass_obj
def results(context: CGConfig, family_id: str):
    """Upload mutant analysis data to GISAID."""

    LOG.info("----------------- GISAID UPLOAD-------------------")

    gisaid_api = GisaidAPI(config=context)
    gsaid_samples: List[GisaidSample] = gisaid_api.get_gisaid_samples(family_id=family_id)
    files: UpploadFiles = UpploadFiles(
        csv_file=gisaid_api.build_gisaid_csv(
            gsaid_samples=gsaid_samples, file_name=f"{family_id}.csv"
        ),
        fasta_file=gisaid_api.build_gisaid_fasta(
            gsaid_samples=gsaid_samples, file_name=f"{family_id}.fasta", family_id=family_id
        ),
        log_file=gisaid_api.new_log_file(family_id=family_id),
    )

    if files:
        gisaid_api.upload(files)
        gisaid_api.file_to_hk(case_id=family_id, file=files.log_file, tags=["gisaid-log"])
        LOG.info("Result")
        files.csv_file.unlink()
        files.fasta_file.unlink()


@gisaid.command()
@click.argument("family_id", required=True)
@click.pass_obj
def completion_file(context: CGConfig, family_id: str):
    """Update mutant completion file in hk."""

    LOG.info("-----------------UPDATE COMPLETION FILE-------------------")

    gisaid_api = GisaidAPI(config=context)
    files: CompletionFiles = gisaid_api.get_completion_files(case_id=family_id)
    completion_data: Dict[str, str] = gisaid_api.get_accession_numbers(log_file=files.log_file)
    gisaid_api.update_completion(
        completion_file=files.completion_file, completion_data=completion_data
    )
