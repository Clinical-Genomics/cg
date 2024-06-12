import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN, FORCE
from cg.constants.nipt import Q30_THRESHOLD
from cg.exc import AnalysisUploadError
from cg.meta.upload.nipt.models import StatinaUploadFiles
from cg.meta.upload.nipt.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def statina():
    """Upload NIPT result files to Statina"""
    pass


@statina.command("case")
@click.argument("case_id", required=True)
@DRY_RUN
@FORCE
@click.pass_obj
def batch(configs: CGConfig, case_id: str, dry_run: bool, force: bool):
    """Loading batch into the NIPT database"""

    LOG.info("*** Statina UPLOAD START ***")

    nipt_upload_api = NiptUploadAPI(configs)
    nipt_upload_api.set_dry_run(dry_run=dry_run)
    statina_files: StatinaUploadFiles = nipt_upload_api.get_statina_files(case_id=case_id)
    if dry_run:
        LOG.info(f"Found file paths for statina upload: {statina_files.json(exclude_none=True)}")
    elif force or nipt_upload_api.flowcell_passed_qc_value(
        case_id=case_id, q30_threshold=Q30_THRESHOLD
    ):
        nipt_upload_api.upload_to_statina_database(statina_files=statina_files)
    else:
        LOG.error(f"Uploading case failed: {case_id}")
        LOG.error(
            f"Flowcell did not pass one of the following QC parameters:\n"
            f"target_reads={nipt_upload_api.target_reads(case_id=case_id)}, Q30_threshold={Q30_THRESHOLD}"
        )
        raise AnalysisUploadError("Upload failed")
