import click

from cg.constants.taxprofiler import TaxprofilerDefaults

OPTION_FROM_START = click.option(
    "--from-start",
    is_flag=True,
    default=False,
    show_default=True,
    help="Start pipeline from the start",
)

OPTION_INSTRUMENT_PLATFORM = click.option(
    "--instrument-platform",
    type=str,
    default=TaxprofilerDefaults.INSTRUMENT_PLATFORM,
    show_default=True,
    help="Instrument platform: Illumina or Oxford Nanopore (default)",
)
