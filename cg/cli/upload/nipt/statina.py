import logging
import click

from cg.meta.upload.nipt.models import StatinaUploadFiles
from cg.meta.upload.nipt.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
def statina():
    """Upload NIPT result files to Statina"""
    pass


@statina.command("case")
@click.argument("case_id", required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def batch(configs: CGConfig, case_id: str, dry_run: bool):
    """Loading batch into the NIPT database"""

    LOG.info("*** Statina UPLOAD START ***")

    nipt_upload_api = NiptUploadAPI(configs)
    nipt_upload_api.set_dry_run(dry_run=dry_run)
    statina_files: StatinaUploadFiles = nipt_upload_api.get_statina_files(case_id=case_id)
    if dry_run:
        LOG.info(f"Found file paths for statina upload: {statina_files.json(exclude_none=True)}")
    else:
        nipt_upload_api.upload_to_statina_database(statina_files=statina_files)
