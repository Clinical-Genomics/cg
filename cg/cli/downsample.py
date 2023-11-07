"""cg module for downsampling reads in a sample."""

import logging
from pathlib import Path
from typing import Tuple

import click

from cg.apps.downsample.downsample import DownsampleAPI
from cg.apps.downsample.utils import store_downsampled_sample_bundle
from cg.constants.constants import DRY_RUN
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def downsample():
    """Downsample reads in a sample."""


@downsample.command(
    "samples",
    help="Downsample reads in one or multiple samples in a case. Usage: \n"
    "For a single sample: cg downsample samples -c supersonicturtle -cn new_case_name -i ACC1234 0.1\n"
    "For multiple samples:cg downsample samples -c supersonicturtle -cn new_case_name -i ACC1234 0.1 -i ACC12324 10",
)
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Case identifier used in statusdb, e.g. supersonicturtle. The case information wil be transferred to the downsampled case.",
)
@click.option(
    "-cn",
    "--case-name",
    required=True,
    help="Case name that is used as name for the downsampled case.",
)
@click.option(
    "-i",
    "--input-data",
    required=True,
    nargs=2,
    multiple=True,
    help="Identifier used in statusdb, e.g. ACC1234567 and the number of reads to down sample to in millions separated by a space"
    " e.g. ACC1234567 30.0. Multiple inputs can be provided.",
)
@DRY_RUN
@click.pass_obj
def downsample_sample(
    context: CGConfig, case_id: str, case_name: str, input_data: Tuple[str, float], dry_run: bool
):
    """Downsample reads in one or multiple samples."""
    downsample_api = DownsampleAPI(config=context, dry_run=dry_run)
    for sample_id, reads in input_data:
        try:
            downsample_api.downsample_sample(
                case_id=case_id,
                sample_id=sample_id,
                number_of_reads=float(reads),
                case_name=case_name,
            )
        except Exception as error:
            LOG.info(repr(error))
            continue


@downsample.command(
    "store",
    help="Store the downsampled fastq files in housekeeper.\n "
    "Make sure the downsample sbtach job has finished before using this command! \n"
    "Usage: cg downsample store ACC123145_2.0M ACC1231_30.0M",
)
@click.argument("sample_ids", type=str, nargs=-1)
@click.pass_obj
def store_downsampled_samples(context: CGConfig, sample_ids: list[str]):
    """Store fastq files for downsampled samples in Housekeeper."""
    for sample_id in sample_ids:
        downsample_dir: str = str(Path(context.downsample_dir, sample_id))
        LOG.debug(f"Searching for fastq files in : {downsample_dir}")
        try:
            store_downsampled_sample_bundle(
                housekeeper_api=context.housekeeper_api,
                sample_id=sample_id,
                fastq_file_output_directory=downsample_dir,
            )
        except Exception as error:
            LOG.info(repr(error))
            continue
