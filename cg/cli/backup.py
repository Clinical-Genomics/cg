import logging

import click

from cg.apps.pdc import PdcApi
from cg.store import Store
from cg.meta.backup import BackupApi

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def backup(context: click.Context):
    """Backup utilities."""
    pass


@backup.command("fetch-flowcell")
@click.option("-f", "--flowcell", help="Retreive a specific flowcell")
@click.option("--dry-run", "dry_run", is_flag=True, 
              help="Don't retrieve from PDC or set flowcell's status")
@click.pass_context
def fetch_flowcell(context: click.Context, dry_run: bool, flowcell: str):
    """Fetch the first flowcell in the requested queue from backup."""
    status_api = Store(context.obj["database"])
    max_flowcells = context.obj.get('max_flowcells', 1250)
    pdc_api = PdcApi()
    backup_api = BackupApi(status=status_api, pdc_api=pdc_api, max_flowcells=max_flowcells)
    if flowcell:
        flowcell_obj = status_api.flowcell(flowcell)
        if flowcell_obj is None:
            LOG.error(f"{flowcell}: not found in database")
            context.abort()
    else:
        flowcell_obj = None

    retrieval_time = backup_api.fetch_flowcell(flowcell_obj=flowcell_obj, dry_run=dry_run)

    if retrieval_time is None:
        if flowcell:
            LOG.info(f"{flowcell}: updating flowcell status to requested")
            if not dry_run:
                flowcell_obj.status = "requested"
                status_api.commit()
    else:
        hours = retrieval_time / 60 / 60
        LOG.info(f"Retrieval time: {hours:.1}h")
