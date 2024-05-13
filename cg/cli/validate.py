import logging

import click

from cg.apps.lims import LimsAPI
from cg.meta.transfer import PoolState, SampleState, TransferLims
from cg.models.cg_config import CGConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.group(name="validate")
@click.pass_obj
def validate_group():
    """Validation of processes in cg."""


@validate_group.command("pacbio-transfer")
def validate_pacbio_transfer(context: CGConfig):
    """Validate that the PacBio transfer is correct."""
    pass
