import click

from cg.constants.constants import Strandedness

OPTION_FROM_START = click.option(
    "--from-start",
    is_flag=True,
    default=False,
    show_default=True,
    help="Start pipeline from start without resuming execution",
)

OPTION_STRANDEDNESS = click.option(
    "--strandedness",
    type=str,
    default=Strandedness.REVERSE,
    show_default=True,
    help="Strandedness: forward, unstranded or reverse (default)",
)

OPTION_REFERENCES = click.option(
    "--genomes_base", type=click.Path(), help="Path to references folder"
)
