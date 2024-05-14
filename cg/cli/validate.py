import logging

import click

from cg.apps.lims import LimsAPI
from cg.meta.transfer import PoolState, SampleState, TransferLims
from cg.models.cg_config import CGConfig
from cg.services.validate_file_transfer_service.validate_pacbio_file_transfer_service import (
    ValidatePacbioFileTransferService,
)


LOG = logging.getLogger(__name__)


@click.group(name="validate")
@click.pass_obj
def validate_group():
    """Validation of processes in cg."""


@click.pass_obj
@validate_group.command("pacbio-transfer")
def validate_pacbio_transfer(context: CGConfig):
    """Validate that the PacBio transfer is correct."""
    validate_service = ValidatePacbioFileTransferService(config=context)
    validate_service.validate_all_transfer_done()
