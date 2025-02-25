"""cg module for downsampling reads in a sample."""

import logging
from pathlib import Path
from typing import Tuple

import rich_click as click

from cg.apps.downsample.downsample import DownsampleAPI
from cg.apps.downsample.utils import store_downsampled_sample_bundle
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def downsample():
    """Downsample reads in a sample."""


@downsample.command(
    "samples",
    help="Downsample reads in one or multiple samples in a case. Usage: \n"
    "For a single sample: cg downsample samples -c supersonicturtle -cn new_case_name -i ACC1234 0.1\n"
    "For multiple samples:cg downsample samples -c supersonicturtle -cn new_case_name -i ACC1234 0.1 -i ACC12324 10\n"
    "If multiple samples are provided possible sample relationships will need to be added using:\n"
    "cg add relationship.",
)
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Case identifier used in statusdb, e.g. supersonicturtle.",
)
@click.option(
    "-cn",
    "--case-name",
    required=True,
    help="Case name that is used as name for the downsampled case.",
)
@click.option(
    "-a",
    "--account",
    required=False,
    default=None,
    help="Please specify the account to use for the downsampling. Defaults to production (production) or development (stage) account if not specified.",
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
    context: CGConfig,
    case_id: str,
    case_name: str,
    account: str | None,
    input_data: Tuple[str, float],
    dry_run: bool,
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
                account=account,
            )
        except Exception as error:
            LOG.info(repr(error))
            continue


@downsample.command(
    "store",
    help="Store the downsampled fastq files in housekeeper.\n "
    "Make sure the downsample sbtach job has finished before using this command! \n"
    "Usage: cg downsample store ACC123145DS2C0M ACC1231DS30C0M",
)
@click.argument("sample_ids", type=str, nargs=-1)
@click.pass_obj
def store_downsampled_samples(context: CGConfig, sample_ids: list[str]):
    """Store fastq files for downsampled samples in Housekeeper."""
    for sample_id in sample_ids:
        downsample_dir: str = str(Path(context.downsample.downsample_dir, sample_id))
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
