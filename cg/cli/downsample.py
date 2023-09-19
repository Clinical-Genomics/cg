"""cg module for downsampling reads in a sample."""

import logging
from typing import List

import click

from cg.apps.downsample.downsample import DownSampleAPI
from cg.apps.downsample.utils import format_downsample_case
from cg.constants.constants import DRY_RUN
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group
def downsample_cmd():
    """Downsample reads in a sample."""
    return


@downsample_cmd.command(
    "samples", short_help="Downsample reads in one or multiple samples in a case."
)
@click.argument(
    "-c" "--case-internal-id",
    required=True,
    short_help="Case identifier used in statusdb, e.g. supersonicturtle",
)
@click.argument(
    "-sr" "--sample-internal-id;reads",
    multiple=True,
    required=True,
    short_help="Identifier used in statusdb, e.g. ACC1234567 and the number of reads to down sample to in millions separated by ;."
    "e.g. ACC1234567;30",
)
@DRY_RUN
def downsample_sample(
    context: CGConfig, case_internal_id: str, sample_internal_id_reads: List[str], dry_run: bool
):
    """Downsample reads in one or multiple samples."""
    for sample_internal_id_read in sample_internal_id_reads:
        downsample_api = DownSampleAPI(
            config=context,
            dry_run=dry_run,
            case_internal_id=case_internal_id,
            sample_reads=sample_internal_id_read,
        )
        downsample_api.downsample_sample()


@downsample_cmd.command(
    "case", short_help="Down sample reads in all samples in a case to the same number of reads."
)
@click.argument(
    "-c",
    "--case_internal_id",
    required=True,
    short_help="Case identifier used in statusdb, e.g. subsonicrabbit",
)
@click.argument(
    "-r",
    "--number_of_reads",
    required=True,
    short_help="Number of reads to down sample to in millions, e.g. 30",
)
@DRY_RUN
def downsample_case(context: CGConfig, case_internal_id: str, number_of_reads: int, dry_run: bool):
    """Downsample reads in all samples in a case."""
    sample_reads: List[str] = format_downsample_case(
        case_internal_id=case_internal_id,
        number_of_reads=number_of_reads,
        status_db=context.status_db,
    )
    for sample_read in sample_reads:
        downsample_api = DownSampleAPI(
            config=context,
            dry_run=dry_run,
            case_internal_id=case_internal_id,
            sample_reads=sample_read,
        )
        downsample_api.downsample_sample()
