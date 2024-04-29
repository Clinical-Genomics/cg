"""Delivery report helpers."""

import logging
from datetime import datetime

import click

from cg.constants import (
    REPORT_SUPPORTED_DATA_DELIVERY,
    REPORT_SUPPORTED_WORKFLOW,
    Workflow,
)
from cg.meta.report.balsamic import BalsamicReportAPI
from cg.meta.report.balsamic_qc import BalsamicQCReportAPI
from cg.meta.report.balsamic_umi import BalsamicUmiReportAPI
from cg.meta.report.mip_dna import MipDNAReportAPI
from cg.meta.report.report_api import ReportAPI
from cg.meta.report.rnafusion import RnafusionReportAPI
from cg.meta.report.taxprofiler import TaxprofilerReportAPI
from cg.meta.report.tomte import TomteReportAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_qc import BalsamicQCAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.meta.workflow.tomte import TomteAnalysisAPI
from cg.store.models import Case

LOG = logging.getLogger(__name__)


def get_report_case(context: click.Context, case_id: str) -> Case:
    """Extracts a case object for delivery report generation."""
    # Default report API (MIP DNA report API)
    report_api: ReportAPI = (
        context.obj.meta_apis.get("report_api")
        if context.obj.meta_apis.get("report_api")
        else MipDNAReportAPI(config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj))
    )
    case: Case = report_api.status_db.get_case_by_internal_id(internal_id=case_id)
    # Missing or not valid internal case ID
    if not case_id or not case:
        LOG.warning("Invalid case ID. Retrieving available cases.")
        workflow: Workflow = (
            report_api.analysis_api.workflow if context.obj.meta_apis.get("report_api") else None
        )
        cases_without_delivery_report: list[Case] = (
            report_api.get_cases_without_delivery_report(workflow=workflow)
            if not context.obj.meta_apis.get("upload_api")
            else report_api.get_cases_without_uploaded_delivery_report(workflow=workflow)
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
                click.echo(f"{case.internal_id} ({case.data_analysis})")
        raise click.Abort
    if case.data_analysis not in REPORT_SUPPORTED_WORKFLOW:
        LOG.error(
            f"The {case.data_analysis} workflow does not support delivery reports (case: {case.internal_id})"
        )
        raise click.Abort
    if case.data_delivery not in REPORT_SUPPORTED_DATA_DELIVERY:
        LOG.error(
            f"The {case.data_delivery} data delivery does not support delivery reports (case: {case.internal_id})"
        )
        raise click.Abort
    return case


def get_report_api(context: click.Context, case: Case) -> ReportAPI:
    """Returns a report API to be used for the delivery report generation."""
    if context.obj.meta_apis.get("report_api"):
        return context.obj.meta_apis.get("report_api")
    return get_report_api_workflow(context, case.data_analysis)


def get_report_api_workflow(context: click.Context, workflow: Workflow) -> ReportAPI:
    """Return the report API given a specific workflow."""
    # Default report API workflow: MIP-DNA
    workflow: Workflow = workflow if workflow else Workflow.MIP_DNA
    dispatch_report_api: dict[Workflow, ReportAPI] = {
        Workflow.BALSAMIC: BalsamicReportAPI(
            config=context.obj, analysis_api=BalsamicAnalysisAPI(config=context.obj)
        ),
        Workflow.BALSAMIC_QC: BalsamicQCReportAPI(
            config=context.obj, analysis_api=BalsamicQCAnalysisAPI(config=context.obj)
        ),
        Workflow.BALSAMIC_UMI: BalsamicUmiReportAPI(
            config=context.obj, analysis_api=BalsamicUmiAnalysisAPI(config=context.obj)
        ),
        Workflow.MIP_DNA: MipDNAReportAPI(
            config=context.obj, analysis_api=MipDNAAnalysisAPI(config=context.obj)
        ),
        Workflow.RNAFUSION: RnafusionReportAPI(
            config=context.obj, analysis_api=RnafusionAnalysisAPI(config=context.obj)
        ),
        Workflow.TAXPROFILER: TaxprofilerReportAPI(
            config=context.obj, analysis_api=TaxprofilerAnalysisAPI(config=context.obj)
        ),
        Workflow.TOMTE: TomteReportAPI(
            config=context.obj, analysis_api=TomteAnalysisAPI(config=context.obj)
        ),
    }
    return dispatch_report_api.get(workflow)


def get_report_analysis_started(
    case: Case, report_api: ReportAPI, analysis_started_at: str | None
) -> datetime:
    """Resolves and returns a valid analysis date."""
    if not analysis_started_at:
        analysis_started_at: datetime = (
            report_api.status_db.get_case_by_internal_id(internal_id=case.internal_id)
            .analyses[0]
            .started_at
        )
    # If there is no analysis for the provided date
    if not report_api.status_db.get_analysis_by_case_entry_id_and_started_at(
        case_entry_id=case.id, started_at_date=analysis_started_at
    ):
        LOG.error(f"There is no analysis started at {analysis_started_at}")
        raise click.Abort
    LOG.info(f"Using analysis started at: {analysis_started_at}")
    return analysis_started_at
