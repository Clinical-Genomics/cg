import logging
from typing import List

import click

from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.report.balsamic_umi import BalsamicUmiReportAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.models.cg_config import CGConfig
from cg.meta.report.api import ReportAPI
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


@click.group("mip-dna")
@click.pass_context
def mip_dna(context: click.Context):
    """Upload MIP-DNA files to Scout"""

    context.obj.meta_apis["report_api"] = MipDNAReportAPI(
        config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj)
    )


@click.group("balsamic")
@click.pass_context
def balsamic(context: click.Context):
    """Upload BALSAMIC files to Scout"""

    context.obj.meta_apis["report_api"] = BalsamicReportAPI(
        config=context.obj, analysis_api=BalsamicAnalysisAPI(config=context.obj)
    )


@click.group("balsamic-umi")
@click.pass_context
def balsamic_umi(context: click.Context):
    """Upload BALSAMIC UMI files to Scout"""

    context.obj.meta_apis["report_api"] = BalsamicUmiReportAPI(
        config=context.obj, analysis_api=BalsamicUmiAnalysisAPI(config=context.obj)
    )


@click.command("delivery-report-to-scout")
@click.argument("case_id", required=False, type=str)
@click.option(
    "-d", "--dry-run", is_flag=True, default=False, help="Run command without uploading to scout"
)
@click.pass_obj
def delivery_report_to_scout(context: CGConfig, case_id: str, dry_run: bool):
    """Fetches a delivery report from housekeeper and uploads it to scout"""

    report_api: ReportAPI = context.meta_apis["report_api"]

    # Missing case ID
    if not case_id:
        LOG.info("Case ID not provided. Retrieving cases with pending reports to upload to Scout.")
        cases_without_delivery_report = report_api.get_cases_without_delivery_report()
        if not cases_without_delivery_report:
            click.echo(click.style("There are no reports to upload to Scout", fg="green"))
        else:
            LOG.error("Provide one of the following case IDs:\n")
            for case_obj in cases_without_delivery_report:
                click.echo(case_obj)

        raise click.Abort

    uploaded_delivery_report_files: List[hk_models.File] = [
        file_obj
        for file_obj in report_api.housekeeper_api.get_files(
            bundle=case_id,
            tags=["delivery-report"],
            version=report_api.housekeeper_api.last_version(case_id).id,
        )
    ]

    if not uploaded_delivery_report_files:
        LOG.error(f"No delivery report was found in housekeeper for case: {case_id}")
        raise FileNotFoundError

    report_path: str = uploaded_delivery_report_files[0].full_path

    if not dry_run:
        report_api.scout_api.upload_delivery_report(
            report_path=report_path, case_id=case_id, update=True
        )


mip_dna.add_command(delivery_report_to_scout)
balsamic.add_command(delivery_report_to_scout)
balsamic_umi.add_command(delivery_report_to_scout)
