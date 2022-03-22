from datetime import datetime
import logging
import sys
from pathlib import Path
from typing import TextIO, Optional

import click
from cg.cli.upload.delivery_report import delivery_report_to_scout
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.exc import DeliveryReportError, CgError
from cg.meta.report.api import ReportAPI
from cg.models.cg_config import CGConfig
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)

ARGUMENT_CASE_ID = click.argument("case_id", required=True, type=str)
OPTION_STARTED_AT = click.option(
    "--analysis-started-at",
    help="Retrieve analysis started at a specific date (i.e.  '2020-05-28  12:00:46')",
)
OPTION_FORCE_REPORT = click.option(
    "-f", "--force", "force_report", is_flag=True, default=False, help="Overrule report validation"
)
OPTION_DRY_RUN = click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Print to console instead of generating an html report file",
)


@click.command("available-delivery-reports")
@OPTION_FORCE_REPORT
@OPTION_DRY_RUN
@click.pass_context
def available_delivery_reports(context: click.Context, force_report: bool, dry_run: bool):
    """Generates delivery reports for all cases that need one and stores them in housekeeper"""

    report_api: ReportAPI = context.obj.meta_apis["report_api"]
    exit_code = EXIT_SUCCESS

    click.echo(click.style("--------------- AVAILABLE DELIVERY REPORTS ---------------"))

    for analysis_obj in report_api.get_cases_without_delivery_report():
        case_id = analysis_obj.family.internal_id
        LOG.info("Uploading delivery report for case: %s", case_id)
        try:
            context.invoke(
                delivery_report,
                case_id=analysis_obj.family.internal_id,
                force_report=force_report,
                dry_run=dry_run,
            )
        except FileNotFoundError as error:
            LOG.error(
                "The delivery report generation is missing a file for case: %s, %s",
                case_id,
                error,
            )
            exit_code = EXIT_FAIL
        except (CgError, DeliveryReportError) as error:
            LOG.error(
                "The delivery report generation failed for case: %s, %s",
                case_id,
                error.message,
            )
            exit_code = EXIT_FAIL
        except Exception as error:
            LOG.error(
                "Unspecified error when uploading delivery report for case: %s, %s",
                case_id,
                error.message,
            )
            exit_code = EXIT_FAIL

    sys.exit(exit_code)


@click.command("delivery-report")
@ARGUMENT_CASE_ID
@OPTION_FORCE_REPORT
@OPTION_DRY_RUN
@OPTION_STARTED_AT
@click.pass_obj
def delivery_report(
    context: click.Context,
    cg_context: CGConfig,
    case_id: str,
    force_report: bool,
    dry_run: bool,
    analysis_started_at: str = None,
):
    """Generates a delivery report for a case and stores it in housekeeper"""

    click.echo(click.style("--------------- DELIVERY REPORT ---------------"))

    report_api: ReportAPI = cg_context.meta_apis["report_api"]

    # Invalid internal case ID
    if not case_id or not report_api.status_db.family(case_id):
        LOG.error("Provide a case, suggestions:")
        for case_obj in report_api.get_cases_without_delivery_report():
            click.echo(case_obj)

        raise click.Abort

    # Analysis date retrieval
    if not analysis_started_at:
        analysis_started_at: datetime = report_api.status_db.family(case_id).analyses[0].started_at

    LOG.info("Using analysis started at: %s", analysis_started_at)

    # Dry run: prints the HTML report to console
    if dry_run:
        delivery_report_html: str = report_api.create_delivery_report(
            case_id, analysis_started_at, force_report
        )
        click.echo(delivery_report_html)
        return

    delivery_report_file: TextIO = report_api.create_delivery_report_file(
        case_id,
        file_path=Path(report_api.analysis_api.root, case_id),
        analysis_date=analysis_started_at,
        force_report=force_report,
    )

    hk_report_file: Optional[hk_models.File] = report_api.add_delivery_report_to_hk(
        delivery_report_file, case_id, analysis_started_at
    )

    if hk_report_file:
        click.echo(click.style("Uploaded delivery report to housekeeper", fg="green"))
    else:
        click.echo(click.style("Delivery report already uploaded to housekeeper", fg="yellow"))

    context.invoke(delivery_report_to_scout, case_id, dry_run)
    report_api.update_delivery_report_date(case_id=case_id, analysis_date=analysis_started_at)
