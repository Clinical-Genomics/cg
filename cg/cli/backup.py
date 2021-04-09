import logging
from typing import Optional

import click
from cg.apps.pdc import PdcApi
from cg.meta.backup import BackupApi
from cg.store import Store, models

LOG = logging.getLogger(__name__)
MAX_FLOWCELLS_ON_DISK = 1250  # Increased by 250 when the previous limit of 1000 was reached


@click.group()
def backup():
    """Backup utilities."""
    pass


@backup.command("fetch-flowcell")
@click.option("-f", "--flowcell", help="Retrieve a specific flowcell")
@click.option("--dry-run", is_flag=True, help="Don't retrieve from PDC or set flowcell's status")
@click.pass_context
def fetch_flowcell(context: click.Context, dry_run: bool, flowcell: str):
    """Fetch the first flowcell in the requested queue from backup."""
    status_api: Store = context.obj["status_db"]
    max_flowcells_on_disk: int = context.obj.get("max_flowcells", MAX_FLOWCELLS_ON_DISK)
    root_dir: str = context.obj["backup"]["root"]
    pdc_api = PdcApi()
    backup_api = BackupApi(
        status=status_api,
        pdc_api=pdc_api,
        max_flowcells_on_disk=max_flowcells_on_disk,
        root_dir=root_dir,
    )
    flowcell_obj: Optional[models.Flowcell] = None
    if flowcell:
        flowcell_obj: Optional[models.Flowcell] = status_api.flowcell(flowcell)
        if flowcell_obj is None:
            LOG.error(f"{flowcell}: not found in database")
            raise click.Abort

    retrieval_time: float = backup_api.fetch_flowcell(flowcell_obj=flowcell_obj, dry_run=dry_run)

    if retrieval_time:
        hours = retrieval_time / 60 / 60
        LOG.info(f"Retrieval time: {hours:.1}h")
        return

    if not flowcell:
        return

    if not dry_run:
        LOG.info(f"{flowcell}: updating flowcell status to requested")
        flowcell_obj.status = "requested"
        status_api.commit()
