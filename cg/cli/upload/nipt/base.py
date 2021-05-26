""" Upload NIPT results via the CLI"""

import logging
from .ftp import ftp
from .niptool import niptool

import click

from cg.meta.upload.nipt import NiptUploadAPI
from cg.models.cg_config import CGConfig
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group()
def nipt():
    """Upload NIPT result files"""
    pass


nipt.add_command(ftp)
nipt.add_command(niptool)
