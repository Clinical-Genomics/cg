"""cg module for downsampling reads in a sample."""

import logging
from typing import List

import click

from cg.apps.downsample.downsample import DownSampleAPI
from cg.constants.constants import DRY_RUN
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group
def down_sample_cmd():
    """Downsample reads in a sample."""
    return


@down_sample_cmd.command(
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
    short_help="Identifier used in statusdb, e.g. ACC1234567 separated by the number of reads to down sample to in millions."
    "e.g. ACC1234567;30",
)
@DRY_RUN
def down_sample_sample(case_internal_id: str, sample_internal_id_reads: List[str], dry_run: bool):
    """Downsample reads in one or multiple samples."""
    for sample_internal_id_read in sample_internal_id_reads:
        down_sample_api = DownSampleAPI(
            config=CGConfig,
            dry_run=dry_run,
            case_internal_id=case_internal_id,
            sample_reads=sample_internal_id_read,
        )
        down_sample_api.down_sample_sample()
