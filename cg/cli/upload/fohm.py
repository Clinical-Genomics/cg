import logging
from typing import Optional, List

import click

from cg.meta.upload.fohm.fohm import FOHMUploadAPI
from cg.meta.upload.gisaid import GisaidAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)

ARGUMENT_DATE = click.argument(
    "datestr",
    type=str,
    required=False,
)
OPTION_CASES = click.option(
    "cases",
    "-c",
    multiple=True,
    type=str,
    required=True,
    help="CG internal id of cases to aggregate for daily delivery",
)
OPTION_DRY_RUN = click.option(
    "dry_run", "--dry-run", is_flag=True, default=False, help="Run command in dry run"
)


@click.group()
@click.pass_obj
def fohm(context: CGConfig):
    pass


@fohm.command("aggregate-delivery")
@OPTION_CASES
@OPTION_DRY_RUN
@ARGUMENT_DATE
@click.pass_obj
def aggregate_delivery(
    context: CGConfig, cases: list, dry_run: bool = False, datestr: Optional[str] = None
):
    """Re-aggregates delivery files for FOHM and saves them to default working directory"""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    fohm_api.set_cases_to_aggregate(cases=cases)
    fohm_api.create_daily_delivery_folders()
    fohm_api.append_metadata_to_aggregation_df()
    fohm_api.create_komplettering_reports()
    fohm_api.create_pangolin_reports()
    fohm_api.link_sample_rawdata_files()


@fohm.command("create-komplettering")
@OPTION_CASES
@OPTION_DRY_RUN
@ARGUMENT_DATE
@click.pass_obj
def create_komplettering(
    context: CGConfig, cases: list, dry_run: bool = False, datestr: Optional[str] = None
):
    """Re-aggregates komplettering files for FOHM and saves them to default working directory"""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    fohm_api.set_cases_to_aggregate(cases=cases)
    fohm_api.create_daily_delivery_folders()
    fohm_api.append_metadata_to_aggregation_df()
    fohm_api.create_komplettering_reports()


@fohm.command("preprocess-all")
@OPTION_CASES
@OPTION_DRY_RUN
@ARGUMENT_DATE
@click.pass_obj
def preprocess_all(
    context: CGConfig, cases: list, dry_run: bool = False, datestr: Optional[str] = None
):
    """Create all FOHM upload files, upload to GISAID, sync SFTP and mail reports for all provided cases"""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    gisaid_api = GisaidAPI(config=context)
    cases = list(cases)
    upload_cases: List = []
    for case_id in cases:
        try:
            gisaid_api.upload(case_id=case_id)
            fohm_api.update_upload_started_at(case_id=case_id)
            LOG.info(f"Upload of case {case_id} to GISAID was successful")
            upload_cases.append(case_id)
        except Exception as error:
            LOG.error(
                f"Upload of case {case_id} to GISAID unseccessful {error}, case {case_id} "
                f"will be removed from delivery batch"
            )
    fohm_api.set_cases_to_aggregate(cases=upload_cases)
    fohm_api.create_daily_delivery_folders()
    fohm_api.append_metadata_to_aggregation_df()
    fohm_api.create_komplettering_reports()
    fohm_api.create_pangolin_reports()
    fohm_api.link_sample_rawdata_files()
    fohm_api.sync_files_sftp()
    fohm_api.send_mail_reports()
    for case_id in upload_cases:
        fohm_api.update_uploaded_at(case_id=case_id)
    LOG.info("Upload to FOHM completed")


@fohm.command("upload-rawdata")
@ARGUMENT_DATE
@OPTION_DRY_RUN
@click.pass_obj
def upload_rawdata(context: CGConfig, dry_run: bool = False, datestr: Optional[str] = None):
    """Deliver files in daily upload directory via sftp"""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    fohm_api.sync_files_sftp()


@fohm.command("send-reports")
@ARGUMENT_DATE
@OPTION_DRY_RUN
@click.pass_obj
def send_reports(context: CGConfig, dry_run: bool = False, datestr: Optional[str] = None):
    """Send all komplettering reports found in current daily directory to target recipients"""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    fohm_api.send_mail_reports()
