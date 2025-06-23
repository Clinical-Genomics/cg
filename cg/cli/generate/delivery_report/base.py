"""Commands to generate delivery reports."""

import logging
import sys
from datetime import datetime
from pathlib import Path

import rich_click as click
from housekeeper.store.models import Version

from cg.cli.generate.delivery_report.options import ARGUMENT_CASE_ID, OPTION_WORKFLOW
from cg.cli.generate.delivery_report.utils import (
    get_analysis_for_delivery_report,
    get_report_api,
    get_report_api_workflow,
    get_report_case,
)
from cg.constants import EXIT_FAIL, EXIT_SUCCESS, Workflow
from cg.constants.cli_options import DRY_RUN, FORCE
from cg.exc import CgError
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


@click.command("delivery-report")
@ARGUMENT_CASE_ID
@FORCE
@DRY_RUN
@click.pass_context
def generate_delivery_report(
    context: click.Context,
    case_id: str,
    force: bool,
    dry_run: bool,
) -> None:
    """Creates a delivery report for the latest analysis of the provided case."""
    click.echo(click.style("--------------- DELIVERY REPORT ---------------"))
    case: Case = get_report_case(context=context, case_id=case_id)
    report_api: DeliveryReportAPI = get_report_api(context=context, case=case)
    analysis: Analysis = get_analysis_for_delivery_report(case)

    # Dry run: prints the HTML report to console
    if dry_run:
        delivery_report_html: str = report_api.get_delivery_report_html(
            analysis=analysis, force=force
        )
        click.echo(delivery_report_html)
        return

    version: Version = report_api.housekeeper_api.get_version_by_id(analysis.housekeeper_version_id)
    delivery_report: str | None = report_api.get_delivery_report_from_hk(
        case_id=case_id, version=version
    )
    if delivery_report:
        click.echo(
            click.style(f"Delivery report already in housekeeper: {delivery_report}", fg="yellow")
        )
        return

    created_delivery_report: Path = report_api.write_delivery_report_file(
        directory=Path(report_api.analysis_api.root, case_id),
        analysis=analysis,
        force=force,
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
    report_api.update_delivery_report_date(analysis)


@click.command("available-delivery-reports")
@OPTION_WORKFLOW
@FORCE
@DRY_RUN
@click.pass_context
def generate_available_delivery_reports(
    context: click.Context, workflow: Workflow, force: bool, dry_run: bool
) -> None:
    """Generates delivery reports for all cases that need one and stores them in Housekeeper."""

    click.echo(click.style("--------------- AVAILABLE DELIVERY REPORTS ---------------"))

    exit_code = EXIT_SUCCESS

    report_api: DeliveryReportAPI = get_report_api_workflow(context=context, workflow=workflow)
    context.obj.meta_apis["report_api"] = report_api if workflow else None

    cases_without_delivery_report = report_api.get_cases_without_delivery_report(workflow)
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
            LOG.info(f"Generating delivery report for case: {case_id}")
            try:
                context.invoke(
                    generate_delivery_report,
                    case_id=case_id,
                    force=force,
                    dry_run=dry_run,
                )
            except FileNotFoundError as error:
                LOG.error(
                    f"The delivery report generation is missing a file for case: {case_id}, {error}"
                )
                exit_code = EXIT_FAIL
            except CgError as error:
                LOG.error(f"The delivery report generation failed for case: {case_id}, {error}")
                exit_code = EXIT_FAIL
            except Exception as error:
                LOG.error(
                    f"Unspecified error when generating the delivery report for case: {case_id}, {error}"
                )
                exit_code = EXIT_FAIL

    sys.exit(exit_code)
