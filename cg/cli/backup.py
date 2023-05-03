"""Backup related CLI commands."""
import logging
from typing import Optional

import click

from cg.constants.constants import DRY_RUN, FlowCellStatus
from cg.meta.backup.backup import BackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Flowcell

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_obj
def backup(context: CGConfig):
    """Backup utilities"""
    pass


@backup.command("fetch-flow-cell")
@click.option("-f", "--flow-cell-id", help="Retrieve a specific flow cell, ex. 'HCK2KDSXX'")
@DRY_RUN
@click.pass_obj
def fetch_flow_cell(context: CGConfig, dry_run: bool, flow_cell_id: Optional[str] = None):
    """Fetch the first flow cell in the requested queue from backup"""

    pdc_api = PdcAPI(binary_path=context.pdc.binary_path, dry_run=dry_run)
    encryption_api = EncryptionAPI(binary_path=context.encryption.binary_path, dry_run=dry_run)
    tar_api = TarAPI(binary_path=context.tar.binary_path, dry_run=dry_run)
    context.meta_apis["backup_api"] = BackupAPI(
        encryption_api=encryption_api,
        encrypt_dir=context.backup.encrypt_dir.dict(),
        status=context.status_db,
        tar_api=tar_api,
        pdc_api=pdc_api,
        root_dir=context.backup.root.dict(),
        dry_run=dry_run,
    )
    backup_api: BackupAPI = context.meta_apis["backup_api"]

    status_api: Store = context.status_db
    flow_cell: Optional[Flowcell] = (
        status_api.get_flow_cell_by_name(flow_cell_name=flow_cell_id) if flow_cell_id else None
    )

    if not flow_cell and flow_cell_id:
        LOG.error(f"{flow_cell_id}: not found in database")
        raise click.Abort

    if not flow_cell_id:
        LOG.info("Fetching first flow cell in queue")

    retrieval_time: Optional[float] = backup_api.fetch_flow_cell(flow_cell=flow_cell)

    if retrieval_time:
        hours = retrieval_time / 60 / 60
        LOG.info(f"Retrieval time: {hours:.1}h")
        return

    if not dry_run and flow_cell:
        LOG.info(f"{flow_cell}: updating flow cell status to {FlowCellStatus.REQUESTED}")
        flow_cell.status = FlowCellStatus.REQUESTED
        status_api.session.commit()
