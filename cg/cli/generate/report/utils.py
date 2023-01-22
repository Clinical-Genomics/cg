"""Delivery report helpers"""

import logging
from datetime import datetime
from typing import Optional

import click
from cgmodels.cg.constants import Pipeline

from cg.constants import REPORT_SUPPORTED_PIPELINES, REPORT_SUPPORTED_DATA_DELIVERY
from cg.meta.report.report_api import ReportAPI
from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.report.balsamic_umi import BalsamicUmiReportAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.store import models

LOG = logging.getLogger(__name__)


def get_report_case(context: click.Context, case_id: str) -> models.Family:
    """Extracts a case object for delivery report generation."""

    # Default report API (MIP DNA report API)
    report_api: ReportAPI = (
        context.obj.meta_apis.get("report_api")
        if context.obj.meta_apis.get("report_api")
        else MipDNAReportAPI(config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj))
    )

    case: models.Family = report_api.status_db.family(case_id)

    # Missing or not valid internal case ID
    if not case_id or not case:
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
            for case in cases_without_delivery_report:
                click.echo(f"{case.internal_id} ({ case.data_analysis})")

        raise click.Abort

    if case.data_analysis not in REPORT_SUPPORTED_PIPELINES:
        LOG.error(
            f"The {case.data_analysis} pipeline does not support delivery reports (case: {case.internal_id})"
        )

    if case.data_delivery not in REPORT_SUPPORTED_DATA_DELIVERY:
        LOG.error(
            f"The {case.data_delivery} data delivery does not support delivery reports (case: {case.internal_id})"
        )

        raise click.Abort

    return case


def get_report_api(context: click.Context, case: models.Family) -> ReportAPI:
    """Returns a report API to be used for the delivery report generation."""

    if context.obj.meta_apis.get("report_api"):
        return context.obj.meta_apis.get("report_api")

    return get_report_api_pipeline(context, case.data_analysis)


def get_report_api_pipeline(context: click.Context, pipeline: Pipeline) -> ReportAPI:
    """Resolves the report API given a specific pipeline."""

    # Default report API pipeline: MIP-DNA
    pipeline = pipeline if pipeline else Pipeline.MIP_DNA

    dispatch_report_api = {
        Pipeline.MIP_DNA: MipDNAReportAPI(
            config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj)
        ),
        Pipeline.BALSAMIC: BalsamicReportAPI(
            config=context.obj, analysis_api=BalsamicAnalysisAPI(config=context.obj)
        ),
        Pipeline.BALSAMIC_UMI: BalsamicUmiReportAPI(
            config=context.obj, analysis_api=BalsamicUmiAnalysisAPI(config=context.obj)
        ),
    }

    return dispatch_report_api.get(pipeline)


def get_report_analysis_started(
    case: models.Family, report_api: ReportAPI, analysis_started_at: Optional[str]
) -> datetime:
    """Resolves and returns a valid analysis date."""

    if not analysis_started_at:
        analysis_started_at: datetime = (
            report_api.status_db.family(case.internal_id).analyses[0].started_at
        )

    # If there is no analysis for the provided date
    if not report_api.status_db.analysis(case, analysis_started_at):
        LOG.error(f"There is no analysis started at {analysis_started_at}")
        raise click.Abort

    LOG.info("Using analysis started at: %s", analysis_started_at)
    return analysis_started_at
