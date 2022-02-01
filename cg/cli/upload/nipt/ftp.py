import logging
from pathlib import Path

import click

from cg.constants.nipt import Q30_THRESHOLD
from cg.exc import AnalysisUploadError
from cg.meta.upload.nipt.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def ftp():
    """Upload NIPT result files to ftp-server"""
    pass


@ftp.command("case")
@click.argument("case_id", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def nipt_upload_case(context: CGConfig, case_id: str, dry_run: bool):
    """Upload the results file of a NIPT case"""
    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(context)
    nipt_upload_api.set_dry_run(dry_run=dry_run)

    if nipt_upload_api.flowcell_passed_qc_value(case_id=case_id, q30_threshold=Q30_THRESHOLD):
        LOG.info("*** NIPT FTP UPLOAD START ***")

        hk_results_file: str = nipt_upload_api.get_housekeeper_results_file(case_id=case_id)
        results_file: Path = nipt_upload_api.get_results_file_path(hk_results_file)

        LOG.info(f"Results file found: {results_file}")
        LOG.info("Starting ftp upload!")

        nipt_upload_api.upload_to_ftp_server(results_file)

        LOG.info("Upload ftp finished!")
    else:
        LOG.error("Uploading case failed: %s", case_id)
        LOG.error(
            f"Flowcell did not pass one of the following QC parameters:\n"
            f"target_reads={nipt_upload_api.target_reads(case_id=case_id)}, Q30_threshold={Q30_THRESHOLD}"
        )
        raise AnalysisUploadError("Upload failed")


@ftp.command("all")
@click.option("--dry-run", is_flag=True)
@click.pass_context
def nipt_upload_all(context: click.Context, dry_run: bool):
    """Upload all available NIPT results files"""

    LOG.info("*** UPLOAD ALL AVAILABLE NIPT RESULTS ***")

    nipt_upload_api = NiptUploadAPI(context.obj)
    upload_nipt_analyses = nipt_upload_api.get_all_upload_analyses()

    for analysis in upload_nipt_analyses:
        case_id = analysis.family.internal_id
        context.invoke(nipt_upload_case, case_id=case_id, dry_run=dry_run)
