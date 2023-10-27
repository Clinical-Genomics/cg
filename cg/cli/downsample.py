"""cg module for downsampling reads in a sample."""

import logging
from typing import Tuple

import click

from cg.apps.downsample.downsample import DownSampleAPI
from cg.constants.constants import DRY_RUN
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def downsample_cmd():
    """Downsample reads in a sample."""


@downsample_cmd.command("samples", help="Downsample reads in one or multiple samples in a case.")
@click.option(
    "-c",
    "--case--id",
    required=True,
    help="Case identifier used in statusdb, e.g. supersonicturtle. The case information wil be transferred.",
)
@click.option(
    "-i",
    "--input",
    required=True,
    multiple=True,
    help="Identifier used in statusdb, e.g. ACC1234567 and the number of reads to down sample to in millions separated by a space."
    "e.g. ACC1234567 30",
)
@DRY_RUN
def downsample_sample(
    context: CGConfig, case_internal_id: str, input_data: Tuple[str, float], dry_run: bool
):
    """Downsample reads in one or multiple samples."""
    for sample_internal_id, reads in input_data:
        try:
            downsample_api = DownSampleAPI(
                config=context,
                dry_run=dry_run,
                case_internal_id=case_internal_id,
                sample_internal_id=sample_internal_id,
                number_of_reads=reads,
            )
            downsample_api.downsample_sample()
        except Exception as error:
            LOG.info(repr(error))
            continue


@downsample_cmd.command(
    "case", help="Down sample reads in all samples in a case to the same number of reads."
)
@click.option(
    "-input",
    "--input",
    required=True,
    help="Case identifier used in statusdb and the number of reads to downsample to in millions.  e.g. subsonicrabbit 30.",
)
@DRY_RUN
def downsample_case(context: CGConfig, input: Tuple[str, float], dry_run: bool):
    """Downsample reads in all samples in a case."""
    ## TO DO; this has to retrieve samples and then loop over samples like above...
    pass
