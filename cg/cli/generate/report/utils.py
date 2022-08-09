"""Delivery report helpers"""

import logging
from datetime import datetime
from typing import Optional

import click
from cgmodels.cg.constants import Pipeline

from cg.constants import REPORT_SUPPORTED_PIPELINES
from cg.meta.report.report_api import ReportAPI
from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.report.balsamic_umi import BalsamicUmiReportAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.store import models

LOG = logging.getLogger(__name__)


def resolve_report_case(context: click.Context, case_id: str) -> models.Family:
    """Resolves case object for delivery report generation"""

    # Default report API (MIP DNA report API)
    report_api: ReportAPI = (
        context.obj.meta_apis.get("report_api")
        if context.obj.meta_apis.get("report_api")
        else MipDNAReportAPI(config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj))
    )

    case_obj = report_api.status_db.family(case_id)

    # Missing or not valid internal case ID
    if not case_id or not case_obj:
        LOG.warning("Invalid case ID. Retrieving available cases.")

        pipeline = (
            report_api.analysis_api.pipeline if context.obj.meta_apis.get("report_api") else None
        )

        cases_without_delivery_report = (
            report_api.get_cases_without_delivery_report(pipeline)
            if not context.obj.meta_apis.get("upload_api")
            else report_api.get_cases_without_uploaded_delivery_report(pipeline)
        )

        if not cases_without_delivery_report:
            click.echo(
                click.style(
                    "There are no valid cases to perform delivery report actions", fg="green"
                )
            )
        else:
            LOG.error("Provide one of the following case IDs:")
            for case_obj in cases_without_delivery_report:
                click.echo(f"{case_obj.internal_id} ({ case_obj.data_analysis})")

        raise click.Abort

    if case_obj.data_analysis not in REPORT_SUPPORTED_PIPELINES:
        LOG.error(
            f"The {case_obj.data_analysis} pipeline does not support delivery reports (case: {case_obj.internal_id})"
        )

        raise click.Abort

    return case_obj


def resolve_report_api(context: click.Context, case_obj: models.Family) -> ReportAPI:
    """Resolves the report API to be used for the delivery report generation"""

    if context.obj.meta_apis.get("report_api"):
        report_api = context.obj.meta_apis.get("report_api")
    else:
        report_api = resolve_report_api_pipeline(context, case_obj.data_analysis)

    return report_api


def resolve_report_api_pipeline(context: click.Context, pipeline: Pipeline) -> ReportAPI:
    """Resolves the report API given a specific pipeline"""

    if pipeline == Pipeline.BALSAMIC:
        # BALSAMIC report API
        report_api = BalsamicReportAPI(
            config=context.obj, analysis_api=BalsamicAnalysisAPI(config=context.obj)
        )
    elif pipeline == Pipeline.BALSAMIC_UMI:
        # BALSAMIC UMI report API
        report_api = BalsamicUmiReportAPI(
            config=context.obj, analysis_api=BalsamicUmiAnalysisAPI(config=context.obj)
        )
    else:
        # Default report API (MIP DNA report API)
        report_api = MipDNAReportAPI(
            config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj)
        )

    return report_api


def resolve_report_analysis_started(
    case_obj: models.Family, report_api: ReportAPI, analysis_started_at: Optional[str]
) -> datetime:
    """Resolves analysis date"""

    if not analysis_started_at:
        analysis_started_at: datetime = (
            report_api.status_db.family(case_obj.internal_id).analyses[0].started_at
        )

    # If there is no analysis for the provided date
    if not report_api.status_db.analysis(case_obj, analysis_started_at):
        LOG.error(f"There is no analysis started at {analysis_started_at}")
        raise click.Abort

    LOG.info("Using analysis started at: %s", analysis_started_at)
    return analysis_started_at
