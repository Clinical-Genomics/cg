import click

from cg.constants.gene_panel import GENOME_BUILD_37, GENOME_BUILD_38

EMAIL_OPTION = click.option("-e", "--email", help="Email to send errors to", type=str)
PRIORITY_OPTION = click.option(
    "-p",
    "--priority",
    default="normal",
    type=click.Choice(["low", "normal", "high"]),
)
START_WITH_PROGRAM = click.option(
    "-sw", "--start-with", help="Start mip from this program.", type=str
)
OPTION_DNA_PANEL_GENOME_BUILD = click.option(
    "--panel-genome-build",
    default=GENOME_BUILD_37,
    type=str,
    help="Set genome build for gene panel export from Scout",
)
OPTION_DRY = click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print to console instead of executing",
)
OPTION_MIP_DRY_RUN = click.option("--mip-dry-run", is_flag=True, help="Run MIP in dry-run mode")
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    type=str,
    help="Set this option to override fetching of panel name from LIMS",
)
OPTION_RNA_PANEL_GENOME_BUILD = click.option(
    "--panel-genome-build",
    default=GENOME_BUILD_38,
    type=str,
    help="Set genome build for gene panel export from Scout",
)
OPTION_SKIP_EVALUATION = click.option(
    "--skip-evaluation",
    "skip_evaluation",
    is_flag=True,
    help="Skip mip qccollect evaluation",
)

ARGUMENT_CASE_ID = click.argument("case_id", required=True, type=str)
