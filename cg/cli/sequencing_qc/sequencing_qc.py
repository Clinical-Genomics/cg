import logging
import click

from cg.models.cg_config import CGConfig
from cg.services.quality_controller.quality_controller_service import QualityControllerService

LOG = logging.getLogger(__name__)


@click.command(name="sequencing-qc", help="Perform sequencing QC")
@click.pass_obj
def sequencing_qc(context: CGConfig):
    sequencing_qc_service: QualityControllerService = context.sequencing_qc_service
