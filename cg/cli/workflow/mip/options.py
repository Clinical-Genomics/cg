import click

from cg.constants.priority import SlurmQos

EMAIL_OPTION = click.option("-e", "--email", help="Email to send errors to", type=str)
PRIORITY_OPTION = click.option(
    "-p",
    "--priority",
    type=click.Choice([SlurmQos.LOW, SlurmQos.NORMAL, SlurmQos.HIGH]),
)
START_AFTER_PROGRAM = click.option(
    "-sa", "--start-after", help="Start mip after this program.", type=str
)
START_WITH_PROGRAM = click.option(
    "-sw", "--start-with", help="Start mip from this program.", type=str
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

OPTION_SKIP_EVALUATION = click.option(
    "--skip-evaluation",
    "skip_evaluation",
    is_flag=True,
    help="Skip mip qccollect evaluation",
)

ARGUMENT_CASE_ID = click.argument("case_id", required=True, type=str)
