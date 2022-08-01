"""Delivery report upload to scout commands"""

import logging

import click

from cg.cli.generate.report.utils import resolve_report_case, resolve_report_api
from cg.cli.generate.report.options import ARGUMENT_CASE_ID
from cg.meta.report.report_api import ReportAPI

LOG = logging.getLogger(__name__)


@click.command("delivery-report-to-scout")
@ARGUMENT_CASE_ID
@click.option(
    "-d", "--dry-run", is_flag=True, default=False, help="Run command without uploading to scout"
)
@click.pass_context
def upload_delivery_report_to_scout(context: click.Context, case_id: str, dry_run: bool):
    """Fetches a delivery report from housekeeper and uploads it to scout"""

    click.echo(click.style("--------------- DELIVERY REPORT UPLOAD ---------------"))

    case_obj = resolve_report_case(context, case_id)
    report_api: ReportAPI = resolve_report_api(context, case_obj)
    report_path = report_api.get_delivery_report_from_hk(case_id)

    if not dry_run:
        report_api.scout_api.upload_delivery_report(
            report_path=report_path, case_id=case_obj.internal_id, update=True
        )
