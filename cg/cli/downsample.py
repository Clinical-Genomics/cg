"""cg module for downsampling reads in a sample."""

import logging
from typing import Tuple

import click

from cg.apps.downsample.downsample import DownSampleAPI
from cg.constants.constants import DRY_RUN
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def downsample():
    """Downsample reads in a sample."""


@downsample.command("samples", help="Downsample reads in one or multiple samples in a case.")
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Case identifier used in statusdb, e.g. supersonicturtle. The case information wil be transferred.",
)
@click.option(
    "-i",
    "--input-data",
    required=True,
    nargs=2,
    multiple=True,
    help="Identifier used in statusdb, e.g. ACC1234567 and the number of reads to down sample to in millions separated by a space."
    " e.g. ACC1234567 30",
)
@DRY_RUN
@click.pass_obj
def downsample_sample(
    context: CGConfig, case_id: str, input_data: Tuple[str, float], dry_run: bool
):
    """Downsample reads in one or multiple samples."""
    for sample_id, reads in input_data:
        try:
            downsample_api = DownSampleAPI(
                config=context,
                dry_run=dry_run,
                case_id=case_id,
                sample_id=sample_id,
                number_of_reads=reads,
            )
            downsample_api.downsample_sample()
        except Exception as error:
            LOG.info(repr(error))
            continue


@downsample.command("store", help="Store the downsampled fastq files in housekeeper.")
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Case identifier used in statusdb, e.g. supersonicturtle. The case information wil be transferred.",
)
@click.option(
    "-i",
    "--input-data",
    required=True,
    nargs=2,
    multiple=True,
    help="Identifier used in statusdb, e.g. ACC1234567 and the number of reads to down sample to in millions separated by a space."
    " e.g. ACC1234567 30",
)
@DRY_RUN
@click.pass_obj
def store_downsampled_samples(
    context: CGConfig, case_id: str, input_data: Tuple[str, float], dry_run: bool
):
    """Downsample reads in one or multiple samples."""
    for sample_id, reads in input_data:
        try:
            downsample_api = DownSampleAPI(
                config=context,
                dry_run=dry_run,
                case_id=case_id,
                sample_id=sample_id,
                number_of_reads=reads,
            )
            downsample_api.add_downsampled_sample_to_housekeeper()
        except Exception as error:
            LOG.info(repr(error))
            continue
