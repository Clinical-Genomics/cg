"""Delivery report upload to scout commands."""

import logging

import rich_click as click
from housekeeper.store.models import Version

from cg.cli.generate.delivery_report.options import ARGUMENT_CASE_ID
from cg.cli.generate.delivery_report.utils import get_report_api, get_report_case
from cg.constants.cli_options import DRY_RUN
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.store.models import Case

LOG = logging.getLogger(__name__)


@click.command("delivery-report-to-scout")
@ARGUMENT_CASE_ID
@click.option(
    "-r", "--re-upload", is_flag=True, default=False, help="Re-upload existing delivery report"
)
@DRY_RUN
@click.pass_context
def upload_delivery_report_to_scout(
    context: click.Context, case_id: str, re_upload: bool, dry_run: bool
) -> None:
    """Fetches a delivery report from Housekeeper and uploads it to Scout."""
    click.echo(click.style("--------------- DELIVERY REPORT UPLOAD ---------------"))
    case: Case = get_report_case(context, case_id)
    report_api: DeliveryReportAPI = get_report_api(context, case)
    version: Version = report_api.housekeeper_api.last_version(case_id)
    delivery_report: str | None = report_api.get_delivery_report_from_hk(
        case_id=case_id, version=version
    )
    if delivery_report and not dry_run:
        report_api.scout_api.upload_delivery_report(
            report_path=delivery_report, case_id=case.internal_id, update=re_upload
        )
        return
    LOG.error("Delivery report not uploaded to Scout")
