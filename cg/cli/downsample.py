"""cg module for downsampling reads in a sample."""

import logging
from pathlib import Path
from typing import Tuple

import click

from cg.apps.downsample.downsample import DownsampleAPI
from cg.apps.downsample.utils import add_downsampled_sample_to_housekeeper
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
            downsample_api = DownsampleAPI(
                config=context,
                dry_run=dry_run,
                case_id=case_id,
                sample_id=sample_id,
                number_of_reads=float(reads),
            )
            downsample_api.downsample_sample()
        except Exception as error:
            LOG.info(repr(error))
            continue


@downsample.command("store", help="Store the downsampled fastq files in housekeeper.")
@click.option(
    "-s",
    "--sample_id",
    required=True,
    multiple=True,
    help="Identifier for the downsampled samples ( e.g. ACC1223432_2.0M) that you would like to store. Can supply multiple.",
)
@DRY_RUN
@click.pass_obj
def store_downsampled_samples(context: CGConfig, sample_ids: list[str]):
    """Store fastq files for downsampled samples in Housekeeper."""
    for sample_id in sample_ids:
        downsample_dir: str = str(Path(context.downsample, sample_id))
        try:
            add_downsampled_sample_to_housekeeper(
                housekeeper_api=context.housekeeper_api,
                sample_id=sample_id,
                fastq_file_output_directory=downsample_dir,
            )
        except Exception as error:
            LOG.info(repr(error))
            continue
