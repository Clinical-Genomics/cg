""" Upload NIPT results via the CLI"""

import logging
import traceback
from typing import Optional

import click

from cg.constants.nipt import Q30_THRESHOLD
from cg.exc import AnalysisUploadError
from cg.meta.upload.nipt import NiptUploadAPI
from cg.store.models import Analysis

from .ftp import ftp
from .ftp import nipt_upload_case as nipt_upload_ftp_case
from .statina import batch, statina

LOG = logging.getLogger(__name__)


@click.group()
def nipt():
    """Upload NIPT result files"""
    pass


@nipt.command("case")
@click.argument("case_id", required=True)
@click.option("--dry-run", is_flag=True)
@click.option("--force", is_flag=True, help="Force upload of case to databases, despite qc")
@click.pass_context
def nipt_upload_case(context: click.Context, case_id: Optional[str], dry_run: bool, force: bool):
    """Upload NIPT result files for a case"""

    LOG.info("*** NIPT UPLOAD START ***")

    if context.invoked_subcommand is not None:
        return

    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(context.obj)
    nipt_upload_api.set_dry_run(dry_run=dry_run)
    if force or nipt_upload_api.flowcell_passed_qc_value(
        case_id=case_id, q30_threshold=Q30_THRESHOLD
    ):
        nipt_upload_api.update_analysis_upload_started_date(case_id)
        context.invoke(batch, case_id=case_id, force=force, dry_run=dry_run)
        context.invoke(nipt_upload_ftp_case, case_id=case_id, force=force, dry_run=dry_run)
        nipt_upload_api.update_analysis_uploaded_at_date(case_id)
        LOG.info("%s: analysis uploaded!", case_id)
    else:
        LOG.error("Uploading case failed: %s", case_id)
        LOG.error(
            f"Flowcell did not pass one of the following QC parameters:\n"
            f"target_reads={nipt_upload_api.target_reads(case_id=case_id)}, Q30_threshold={Q30_THRESHOLD}"
        )
        raise AnalysisUploadError("Upload failed")


@nipt.command("all")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def nipt_upload_all(context: click.Context, dry_run: bool):
    """Upload NIPT result files for all cases"""

    LOG.info("*** NIPT UPLOAD ALL START ***")

    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(context.obj)
    nipt_upload_api.set_dry_run(dry_run=dry_run)

    all_good = True
    analyses: list[Analysis] = nipt_upload_api.get_all_upload_analyses()
    if not analyses:
        LOG.info("No analyses found to upload")
        return

    for analysis in analyses:
        internal_id = analysis.family.internal_id

        if nipt_upload_api.flowcell_passed_qc_value(
            case_id=internal_id, q30_threshold=Q30_THRESHOLD
        ):
            LOG.info("Uploading case: %s", internal_id)
            try:
                context.invoke(nipt_upload_case, case_id=internal_id, dry_run=dry_run)
            except AnalysisUploadError:
                LOG.error(traceback.format_exc())
                all_good = False

    if not all_good:
        raise AnalysisUploadError("Some uploads failed")


nipt.add_command(ftp)
nipt.add_command(statina)
