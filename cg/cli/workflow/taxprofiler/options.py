import click

from cg.constants.taxprofiler import TaxprofilerDefaults

OPTION_FROM_START = click.option(
    "--from_start",
    is_flag=True,
    default=False,
    show_default=True,
    help="Start pipeline from start without resuming execution",
)
