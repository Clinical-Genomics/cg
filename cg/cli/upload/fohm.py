import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN
from cg.exc import ValidationError
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


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def fohm(context: CGConfig):
    pass


@fohm.command("aggregate-delivery")
@OPTION_CASES
@DRY_RUN
@ARGUMENT_DATE
@click.pass_obj
def aggregate_delivery(
    context: CGConfig, cases: list, dry_run: bool = False, datestr: str | None = None
):
    """Re-aggregates delivery files for FOHM and saves them to default working directory."""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    try:
        fohm_api.aggregate_delivery(cases)
    except (ValidationError, TypeError) as error:
        LOG.warning(error)


@fohm.command("create-komplettering")
@OPTION_CASES
@DRY_RUN
@ARGUMENT_DATE
@click.pass_obj
def create_komplettering(
    context: CGConfig, cases: list, dry_run: bool = False, datestr: str | None = None
):
    """Re-aggregates komplettering files for FOHM and saves them to default working directory."""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    try:
        fohm_api.create_and_write_complementary_report(cases)
    except ValidationError as error:
        LOG.warning(error)


@fohm.command("preprocess-all")
@OPTION_CASES
@DRY_RUN
@ARGUMENT_DATE
@click.pass_obj
def preprocess_all(
    context: CGConfig, cases: list, dry_run: bool = False, datestr: str | None = None
):
    """Create all FOHM upload files, upload to GISAID, sync SFTP and mail reports for all provided cases."""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    gisaid_api = GisaidAPI(config=context)
    cases = list(cases)
    upload_cases = []
    for case_id in cases:
        try:
            gisaid_api.upload(case_id=case_id)
            fohm_api.update_upload_started_at(case_id=case_id)
            LOG.info(f"Upload of case {case_id} to GISAID was successful")
            upload_cases.append(case_id)
        except Exception as error:
            LOG.error(
                f"Upload of case {case_id} to GISAID unsuccessful {error}, case {case_id} "
                f"will be removed from delivery batch"
            )
    try:
        fohm_api.aggregate_delivery(upload_cases)
    except ValidationError as error:
        LOG.warning(error)
    fohm_api.sync_files_sftp()
    fohm_api.send_mail_reports()
    for case_id in upload_cases:
        fohm_api.update_uploaded_at(case_id=case_id)
    LOG.info("Upload to FOHM completed")


@fohm.command("upload-rawdata")
@ARGUMENT_DATE
@DRY_RUN
@click.pass_obj
def upload_rawdata(context: CGConfig, dry_run: bool = False, datestr: str | None = None):
    """Deliver files in daily upload directory via sftp."""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    fohm_api.sync_files_sftp()


@fohm.command("send-reports")
@ARGUMENT_DATE
@DRY_RUN
@click.pass_obj
def send_reports(context: CGConfig, dry_run: bool = False, datestr: str | None = None):
    """Send all komplettering reports found in the current daily directory to target recipients."""
    fohm_api = FOHMUploadAPI(config=context, dry_run=dry_run, datestr=datestr)
    fohm_api.send_mail_reports()
