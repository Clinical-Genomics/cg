"""Delivery report specific command options."""

import click

from cg.constants import REPORT_SUPPORTED_WORKFLOW

ARGUMENT_CASE_ID = click.argument(
    "case_id",
    required=False,
    type=str,
)

OPTION_WORKFLOW = click.option(
    "--workflow",
    type=click.Choice(REPORT_SUPPORTED_WORKFLOW),
    help="Limit delivery report generation to a specific workflow",
)

OPTION_STARTED_AT = click.option(
    "--analysis-started-at",
    help="Retrieve analysis started at a specific date (i.e. '2020-05-28  12:00:46')",
)

OPTION_FORCE_REPORT = click.option(
    "-f",
    "--force",
    "force_report",
    is_flag=True,
    default=False,
    help="Overrule report validation",
)

OPTION_DRY_RUN = click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print to console instead of generating an html report file",
)
