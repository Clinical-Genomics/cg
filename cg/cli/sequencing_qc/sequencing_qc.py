import logging
import click

from cg.models.cg_config import CGConfig
from cg.services.sequencing_qc_service.sequencing_qc_service import SequencingQCService

LOG = logging.getLogger(__name__)


@click.command(name="sequencing-qc", help="Perform sequencing QC")
@click.pass_obj
def sequencing_qc(context: CGConfig):
    sequencing_qc_service: SequencingQCService = context.sequencing_qc_service
    LOG.info("Running sequencing QC")
