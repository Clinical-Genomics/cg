import click

from cg.constants.sequencing import SequencingPlatform

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
    default=SequencingPlatform.illumina,
    type=click.Choice([SequencingPlatform.illumina, SequencingPlatform.oxford_nanopore]),
    help="Instrument platform.Set this option to override the default.",
)
