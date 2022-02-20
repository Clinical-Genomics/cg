from datetime import datetime
import logging
import sys
from pathlib import Path
from typing import TextIO, Optional

import click
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.exc import DeliveryReportError
from cg.meta.report.api import ReportAPI
from cg.models.cg_config import CGConfig
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)

ARGUMENT_CASE_ID = click.argument("case_id", required=True, type=str)
OPTION_STARTED_AT = click.option(
    "--analysis-started-at",
    help="Retrieve analysis started at a specific date (i.e.  '2020-05-28  12:00:46')",
)
OPTION_DRY_RUN = click.option(
    "-d", "--dry-run", is_flag=True, default=False, help="Print to console instead of executing"
)


@click.command("available-delivery-reports")
@OPTION_DRY_RUN
@click.pass_context
def available_delivery_reports(context: click.Context, dry_run: bool):
    """Generates delivery reports for all cases that need one and stores them in housekeeper"""

    report_api: ReportAPI = context.obj.meta_apis["report_api"]
    exit_code = EXIT_SUCCESS

    click.echo(click.style("--------------- AVAILABLE_DELIVERY REPORTS ---------------"))

    for analysis_obj in report_api.get_cases_without_delivery_report():
        case_id = analysis_obj.family.internal_id
        LOG.info("Uploading delivery report for the case: %s", case_id)
        try:
            context.invoke(
                delivery_report,
                case_id=analysis_obj.family.internal_id,
                dry_run=dry_run,
            )
        except FileNotFoundError as error:
            LOG.error(
                "The delivery report generation is missing a file for the case: %s, %s",
                case_id,
                error,
            )
            exit_code = EXIT_FAIL
        except DeliveryReportError as error:
            LOG.error(
                "The delivery report generation failed for the case: %s, %s",
                case_id,
                error.message,
            )
            exit_code = EXIT_FAIL
        # except CgError as error:  # TODO
        #    LOG.error(
        #        "Uploading delivery report failed for case: %s, %s",
        #        case_id,
        #        error.message,
        #    )
        #    exit_code = FAIL
        # except Exception:
        #    LOG.error(
        #        "Unspecified error when uploading delivery report for case: %s",
        #        case_id,
        #    )
        #    exit_code = FAIL

    sys.exit(exit_code)


@click.command("delivery-report")
@ARGUMENT_CASE_ID
@OPTION_DRY_RUN
@OPTION_STARTED_AT
@click.pass_obj
def delivery_report(
    context: CGConfig,
    case_id: str,
    dry_run: bool,
    analysis_started_at: str = None,
):
    """Generates a delivery report for a case and stores it in housekeeper"""

    click.echo(click.style("--------------- DELIVERY_REPORT ---------------"))

    report_api: ReportAPI = context.meta_apis["report_api"]

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

    # Dry run: print HTML report to console
    if dry_run:
        delivery_report_html: str = report_api.create_delivery_report(case_id, analysis_started_at)
        click.echo(delivery_report_html)
        return

    delivery_report_file: TextIO = report_api.create_delivery_report_file(
        case_id,
        file_path=Path(report_api.analysis_api.root, case_id),
        analysis_date=analysis_started_at,
    )

    hk_report_file: Optional[hk_models.File] = report_api.add_delivery_report_to_hk(
        delivery_report_file, case_id, analysis_started_at
    )

    if hk_report_file:
        click.echo(click.style("Uploaded delivery report to housekeeper", fg="green"))
    else:
        click.echo(click.style("Delivery report already uploaded to housekeeper", fg="yellow"))

    # TODO
    # context.invoke(delivery_report_to_scout, case_id=case_id)
    # report_api.update_delivery_report_date(
    #     status_api=status_db, case_id=case_id, analysis_date=analysis_started_at
    # )


'''
@click.command("delivery-report-to-scout")
@click.argument("case_id", required=False)
@click.option(
    "-d",
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="run command without uploading to scout",
)
@click.pass_obj
def delivery_report_to_scout(context: CGConfig, case_id: str, dry_run: bool):
    """Fetches an delivery-report from housekeeper and uploads it to scout"""
    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    scout_api: ScoutAPI = context.scout_api

    if not case_id:
        suggest_cases_delivery_report(status_db=status_db, pipeline=Pipeline.MIP_DNA)
        raise click.Abort

    uploaded_delivery_report_files: List[hk_models.File] = [
        file_obj
        for file_obj in housekeeper_api.get_files(
            bundle=case_id,
            tags=["delivery-report"],
            version=housekeeper_api.last_version(case_id).id,
        )
    ]
    if not uploaded_delivery_report_files:
        raise FileNotFoundError(f"No delivery report was found in housekeeper for {case_id}")

    report_path: str = uploaded_delivery_report_files[0].full_path

    LOG.info("uploading delivery report %s to scout for case: %s", report_path, case_id)
    if not dry_run:
        scout_api.upload_delivery_report(report_path=report_path, case_id=case_id, update=True)
    click.echo(click.style("uploaded to scout", fg="green"))

'''
