"""Code for uploading delivery report from the CLI"""
import datetime
import logging
import sys
from pathlib import Path
from typing import List, Optional, TextIO

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Pipeline
from cg.exc import CgError, DeliveryReportError
from cg.meta.report.api import ReportAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from housekeeper.store import models as hk_models

from .utils import suggest_cases_delivery_report

LOG = logging.getLogger(__name__)
SUCCESS = 0
FAIL = 1


@click.command("delivery-reports")
@click.option("-p", "--print", "print_console", is_flag=True, help="print list to console")
@click.option(
    "-f",
    "--force",
    "force_report",
    is_flag=True,
    help="overrule report validation",
)
@click.pass_context
def delivery_reports(context: click.Context, print_console: bool, force_report: bool):
    """Generate delivery reports for all cases that need one"""

    status_db: Store = context.obj.status_db

    click.echo(click.style("----------------- DELIVERY REPORTS ------------------------"))

    exit_code = SUCCESS
    for analysis_obj in status_db.analyses_to_delivery_report(pipeline=Pipeline.MIP_DNA):
        case_id = analysis_obj.family.internal_id
        LOG.info("Uploading delivery report for case: %s", case_id)
        try:

            context.invoke(
                delivery_report,
                case_id=analysis_obj.family.internal_id,
                print_console=print_console,
                force_report=force_report,
            )
        except FileNotFoundError as error:
            LOG.error(
                "Missing file for delivery report creation for case: %s, %s",
                case_id,
                error,
            )
            exit_code = FAIL
        except DeliveryReportError as error:
            LOG.error(
                "Creation of delivery report failed for case: %s, %s",
                case_id,
                error.message,
            )
            exit_code = FAIL
        except CgError as error:
            LOG.error(
                "Uploading delivery report failed for case: %s, %s",
                case_id,
                error.message,
            )
            exit_code = FAIL
        except Exception:
            LOG.error(
                "Unspecified error when uploading delivery report for case: %s",
                case_id,
            )
            exit_code = FAIL
    sys.exit(exit_code)


@click.command("delivery-report")
@click.argument("case_id", required=False)
@click.option(
    "-p",
    "--print",
    "print_console",
    is_flag=True,
    help="print report to console",
)
@click.option(
    "-f",
    "--force",
    "force_report",
    is_flag=True,
    help="overrule report validation",
)
@click.option(
    "--analysis-started-at", help="Use the analysis started at (i.e.  '2020-05-28  12:00:46')"
)
@click.pass_context
def delivery_report(
    context: click.Context,
    case_id: str,
    print_console: bool,
    force_report: bool,
    analysis_started_at: str = None,
) -> None:
    """Generates a delivery report for a case and uploads it to housekeeper and scout

    The report contains data from several sources:

    status-db:
        family
        family.data_analysis        missing on most re-runs
        customer_name
        applications
        accredited
        panels
        samples
        sample.internal_id
        sample.status
        sample.ticket
        sample.million_read_pairs   for sequenced samples, from demux + ready made libraries (rml), not for external
        sample.prepared_at          not for rml and external
        sample.received_at
        sample.sequenced_at         for rml and in-house sequenced samples
        sample.delivered_at

    lims:
        sample.name
        sample.sex
        sample.source               missing on most re-runs
        sample.application
        sample.prep_method          not for rml or external
        sample.sequencing_method    for sequenced samples


    trailblazer:
        sample.mapped_reads
        sample.duplicates
        sample.analysis_sex
        pipeline_version
        genome_build

    chanjo:
        sample.target_coverage
        sample.target_completeness

    scout:
        panel-genes

    calculated:
        today
        sample.processing_time
        report_version

    """

    click.echo(click.style("----------------- DELIVERY_REPORT -------------"))

    analysis_api: MipDNAAnalysisAPI = context.obj.meta_apis["analysis_api"]
    report_api: ReportAPI = context.obj.meta_apis["report_api"]
    status_db: Store = context.obj.status_db
    housekeeper_api: HousekeeperAPI = context.obj.housekeeper_api

    if not case_id or not status_db.family(internal_id=case_id):
        suggest_cases_delivery_report(status_db=status_db, pipeline=Pipeline.MIP_DNA)
        raise click.Abort

    if not analysis_started_at:
        analysis_started_at: datetime.datetime = status_db.family(case_id).analyses[0].started_at

    LOG.info("Using analysis started at: %s", analysis_started_at)

    if print_console:
        delivery_report_html: str = report_api.create_delivery_report(
            case_id, analysis_started_at, force_report
        )
        click.echo(delivery_report_html)
        return

    delivery_report_file: TextIO = report_api.create_delivery_report_file(
        case_id,
        file_path=Path(analysis_api.root, case_id),
        accept_missing_data=force_report,
        analysis_date=analysis_started_at,
    )

    added_file: Optional[hk_models.File] = report_api.add_delivery_report_to_hk(
        delivery_report_file, housekeeper_api, case_id, analysis_started_at
    )

    if added_file:
        click.echo(click.style("Uploaded to housekeeper", fg="green"))
    else:
        click.echo(click.style("Already uploaded to housekeeper, skipping", fg="yellow"))

    context.invoke(delivery_report_to_scout, case_id=case_id)
    report_api.update_delivery_report_date(
        status_api=status_db, case_id=case_id, analysis_date=analysis_started_at
    )


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
