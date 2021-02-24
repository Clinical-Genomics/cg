import click

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
OPTION_DRY = click.option(
    "-d",
    "--dry-run",
    "dry_run",
    is_flag=True,
    default=False,
    help="Print to console instead of executing",
)
OPTION_PANEL_BED = click.option(
    "--panel-bed",
    type=str,
    help="Set this option to override fetching of panel name from LIMS",
)

ARGUMENT_CASE_ID = click.argument("case_id", required=True, type=str)
