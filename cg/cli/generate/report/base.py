"""Commands to generate delivery reports."""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from housekeeper.store.models import Version

from cg.cli.generate.report.options import (
    ARGUMENT_CASE_ID,
    OPTION_FORCE_REPORT,
    OPTION_DRY_RUN,
    OPTION_STARTED_AT,
    OPTION_PIPELINE,
)
from cg.cli.generate.report.utils import (
    get_report_case,
    get_report_api,
    get_report_analysis_started,
    get_report_api_pipeline,
)
from cg.constants import EXIT_SUCCESS, EXIT_FAIL, Pipeline
from cg.exc import CgError
from cg.meta.report.report_api import ReportAPI
from cg.store.models import Family

LOG = logging.getLogger(__name__)


@click.command("delivery-report")
@ARGUMENT_CASE_ID
@OPTION_FORCE_REPORT
@OPTION_DRY_RUN
@OPTION_STARTED_AT
@click.pass_context
def generate_delivery_report(
    context: click.Context,
    case_id: str,
    force_report: bool,
    dry_run: bool,
    analysis_started_at: str = None,
) -> None:
    """Creates a delivery report for the provided case."""
    click.echo(click.style("--------------- DELIVERY REPORT ---------------"))
    case: Family = get_report_case(context, case_id)
    report_api: ReportAPI = get_report_api(context, case)
    analysis_date: datetime = get_report_analysis_started(case, report_api, analysis_started_at)

    # Dry run: prints the HTML report to console
    if dry_run:
        delivery_report_html: str = report_api.create_delivery_report(
            case_id, analysis_date, force_report
        )
        click.echo(delivery_report_html)
        return

    version: Version = report_api.housekeeper_api.version(bundle=case_id, date=analysis_date)
    delivery_report: Optional[str] = report_api.get_delivery_report_from_hk(
        case_id=case_id, version=version
    )
    if delivery_report:
        click.echo(
            click.style(f"Delivery report already in housekeeper: {delivery_report}", fg="yellow")
        )
        return

    created_delivery_report: Path = report_api.create_delivery_report_file(
        case_id=case_id,
        directory=Path(report_api.analysis_api.root, case_id),
        analysis_date=analysis_date,
        force_report=force_report,
    )
    report_api.add_delivery_report_to_hk(
        case_id=case_id, delivery_report_file=created_delivery_report, version=version
    )
    click.echo(
        click.style(
            f"Uploaded delivery report to housekeeper: {created_delivery_report.as_posix()}",
            fg="green",
        )
    )
    report_api.update_delivery_report_date(case=case, analysis_date=analysis_date)


@click.command("available-delivery-reports")
@OPTION_PIPELINE
@OPTION_FORCE_REPORT
@OPTION_DRY_RUN
@click.pass_context
def generate_available_delivery_reports(
    context: click.Context, pipeline: Pipeline, force_report: bool, dry_run: bool
) -> None:
    """Generates delivery reports for all cases that need one and stores them in housekeeper."""

    click.echo(click.style("--------------- AVAILABLE DELIVERY REPORTS ---------------"))

    exit_code = EXIT_SUCCESS

    report_api: ReportAPI = get_report_api_pipeline(context, pipeline)
    context.obj.meta_apis["report_api"] = report_api if pipeline else None

    cases_without_delivery_report = report_api.get_cases_without_delivery_report(pipeline)
    if not cases_without_delivery_report:
        click.echo(
            click.style(
                f"There are no cases available to generate delivery reports ({datetime.now()})",
                fg="green",
            )
        )
    else:
        for case in cases_without_delivery_report:
            case_id: str = case.internal_id
            LOG.info("Generating delivery report for case: %s", case_id)
            try:
                context.invoke(
                    generate_delivery_report,
                    case_id=case_id,
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
            except CgError as error:
                LOG.error(
                    "The delivery report generation failed for case: %s, %s",
                    case_id,
                    error,
                )
                exit_code = EXIT_FAIL
            except Exception as error:
                LOG.error(
                    "Unspecified error when generating the delivery report for case: %s, %s",
                    case_id,
                    error,
                )
                exit_code = EXIT_FAIL

    sys.exit(exit_code)
