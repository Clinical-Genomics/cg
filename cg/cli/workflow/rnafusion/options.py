import click

from cg.constants.rnafusion import RNAFUSION_STRANDEDNESS_DEFAULT

OPTION_FROM_START = click.option(
    "--from_start",
    is_flag=True,
    default=False,
    show_default=True,
    help="Start pipeline from start without resuming execution",
)

OPTION_STRANDEDNESS = click.option(
    "--strandedness",
    type=str,
    default=RNAFUSION_STRANDEDNESS_DEFAULT,
    show_default=True,
    help="Strandedness: forward, unstranded or reverse (default)",
)

OPTION_REFERENCES = click.option(
    "--genomes_base", type=click.Path(), help="Path to references folder"
)
OPTION_TRIM = click.option(
    "--trim",
    is_flag=True,
    default=True,
    show_default=True,
    help="Preform trimming of reads to 75 bp",
)
OPTION_FUSIONINSPECTOR_FILTER = click.option(
    "--fusioninspector_filter",
    is_flag=True,
    default=True,
    show_default=True,
    help="Feed filtered fusionreport fusions to fusioninspector",
)
OPTION_ALL = click.option(
    "--all", is_flag=True, default=True, show_default=True, help="Run all analysis tools"
)
OPTION_PIZZLY = click.option(
    "--pizzly", is_flag=True, default=False, show_default=True, help="Run pizzly analysis tool"
)
OPTION_SQUID = click.option(
    "--squid", is_flag=True, default=False, show_default=True, help="Run squid analysis tool"
)
OPTION_STARFUSION = click.option(
    "--starfusion",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run starfusion analysis tool",
)
OPTION_FUSIONCATCHER = click.option(
    "--fusioncatcher",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run fusioncatcher analysis tool",
)
OPTION_ARRIBA = click.option(
    "--arriba", is_flag=True, default=False, show_default=True, help="Run arriba analysis tool"
)
