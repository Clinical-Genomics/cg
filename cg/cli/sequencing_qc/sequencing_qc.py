import logging

import rich_click as click

from cg.models.cg_config import CGConfig
from cg.services.sequencing_qc_service.sequencing_qc_service import SequencingQCService

LOG = logging.getLogger(__name__)


@click.command(name="sequencing-qc", help="Perform sequencing QC")
@click.pass_obj
def sequencing_qc(context: CGConfig):
    service: SequencingQCService = context.sequencing_qc_service
    succeeded: bool = service.run_sequencing_qc()
    if not succeeded:
        raise click.Abort
