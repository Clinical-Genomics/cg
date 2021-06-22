import logging
from pathlib import Path

import click

from cg.meta.upload.nipt.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig
from cg.store import Store

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
    LOG.info("*** NIPT FTP UPLOAD START ***")

    nipt_upload_api: NiptUploadAPI = NiptUploadAPI(context)
    nipt_upload_api.set_dry_run(dry_run=dry_run)

    hk_results_file: str = nipt_upload_api.get_housekeeper_results_file(case_id=case_id)
    results_file: Path = nipt_upload_api.get_results_file_path(hk_results_file)
    LOG.info(f"Results file found: {results_file}")
    LOG.info(f"Starting ftp upload!")
    nipt_upload_api.upload_to_ftp_server(results_file)
    LOG.info(f"Upload ftp finished!")


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
