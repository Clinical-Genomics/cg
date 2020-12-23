"""Code for uploading delivery report from the CLI"""
import datetime as dt
import logging
import sys
from pathlib import Path

import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import Pipeline
from cg.exc import CgError, DeliveryReportError

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
def delivery_reports(context, print_console, force_report):
    """Generate delivery reports for all cases that need one"""

    click.echo(click.style("----------------- DELIVERY REPORTS ------------------------"))

    exit_code = SUCCESS
    for analysis_obj in context.obj["status_db"].analyses_to_delivery_report(
        pipeline=Pipeline.MIP_DNA
    ):
        case_id = analysis_obj.family.internal_id
        LOG.info("Uploading delivery report for case: %s", case_id)
        try:

            context.invoke(
                delivery_report,
                family_id=analysis_obj.family.internal_id,
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
@click.argument("family_id", required=False)
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
@click.pass_context
def delivery_report(context, family_id, print_console, force_report):
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

    def _add_delivery_report_to_hk(
        delivery_report_file: Path, hk_api: HousekeeperAPI, family_id: str
    ):
        delivery_report_tag_name = "delivery-report"
        version_obj = hk_api.last_version(family_id)
        uploaded_delivery_report_files = hk_api.get_files(
            bundle=family_id,
            tags=[delivery_report_tag_name],
            version=version_obj.id,
        )
        number_of_delivery_reports = len(uploaded_delivery_report_files.all())
        is_bundle_missing_delivery_report = number_of_delivery_reports == 0

        if is_bundle_missing_delivery_report:
            file_obj = hk_api.add_file(
                delivery_report_file.name, version_obj, delivery_report_tag_name
            )
            hk_api.include_file(file_obj, version_obj)
            hk_api.add_commit(file_obj)
            return file_obj

        return None

    def _update_delivery_report_date(status_api, case_id: str):
        family_obj = status_api.family(case_id)
        analysis_obj = family_obj.analyses[0]
        analysis_obj.delivery_report_created_at = dt.datetime.now()
        status_api.commit()

    report_api = context.obj["report_api"]

    if not family_id:
        suggest_cases_delivery_report(context)
        context.abort()

    if print_console:
        delivery_report_html = report_api.create_delivery_report(family_id, force_report)
        click.echo(delivery_report_html)
        return

    status_api = context.obj["status_db"]
    mip_dna_root_dir = context.obj["mip-rd-dna"]["root"]
    hk_api = context.obj["housekeeper_api"]

    delivery_report_file = report_api.create_delivery_report_file(
        family_id,
        file_path=Path(mip_dna_root_dir, family_id),
        accept_missing_data=force_report,
    )
    added_file = _add_delivery_report_to_hk(delivery_report_file, hk_api, family_id)

    if added_file:
        click.echo(click.style("uploaded to housekeeper", fg="green"))
    else:
        click.echo(click.style("already uploaded to housekeeper, skipping", fg="yellow"))

    context.invoke(delivery_report_to_scout, case_id=family_id)
    _update_delivery_report_date(status_api, family_id)


@click.command("delivery-report-to-scout")
@click.argument("case_id", required=False)
@click.option(
    "-d",
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="run command without uploading to " "scout",
)
@click.pass_context
def delivery_report_to_scout(context, case_id: str, dry_run: bool):
    """Fetches an delivery-report from housekeeper and uploads it to scout"""

    def _add_delivery_report_to_scout(context, path: Path, case_id: str):
        scout_api = ScoutAPI(context.obj)
        scout_api.upload_delivery_report(path, case_id, update=True)

    def _get_delivery_report_from_hk(hk_api: HousekeeperAPI, family_id):
        delivery_report_tag_name = "delivery-report"
        version_obj = hk_api.last_version(family_id)
        uploaded_delivery_report_files = hk_api.get_files(
            bundle=family_id,
            tags=[delivery_report_tag_name],
            version=version_obj.id,
        )

        if uploaded_delivery_report_files.count() == 0:
            raise FileNotFoundError(f"No delivery report was found in housekeeper for {family_id}")

        return uploaded_delivery_report_files[0].full_path

    if not case_id:
        suggest_cases_delivery_report(context)
        context.abort()

    hk_api = context.obj["housekeeper_api"]
    report = _get_delivery_report_from_hk(hk_api, case_id)

    LOG.info("uploading delivery report %s to scout for case: %s", report, case_id)
    if not dry_run:
        _add_delivery_report_to_scout(context, report, case_id)
    click.echo(click.style("uploaded to scout", fg="green"))
