import click

from cg.constants.taxprofiler import TaxprofilerDefaults
from cg.constants.constants import InstrumentPlatform

OPTION_FROM_START = click.option(
    "--from-start",
    is_flag=True,
    default=False,
    show_default=True,
    help="Start pipeline from the start",
)

OPTION_INSTRUMENT_PLATFORM = click.option(
    "--instrument-platform",
    show_default=True,
    default=InstrumentPlatform.illumina,
    type=click.Choice([InstrumentPlatform.illumina, InstrumentPlatform.oxford_nanopore]),
    help="Instrument platform.Set this option to override the default.",
)
