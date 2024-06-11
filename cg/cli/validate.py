import logging

import click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.models.cg_config import CGConfig
from cg.services.validate_file_transfer_service.validate_pacbio_file_transfer_service import (
    ValidatePacbioFileTransferService,
)


LOG = logging.getLogger(__name__)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def validate():
    """Validation of processes in cg."""


@validate.command("pacbio-transfer")
@click.pass_obj
def validate_pacbio_transfer(context: CGConfig):
    """Validate that the PacBio transfer is correct."""
    validate_service = ValidatePacbioFileTransferService(config=context)
    validate_service.validate_all_transfer_done()
