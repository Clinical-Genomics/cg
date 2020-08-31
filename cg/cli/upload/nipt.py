"""Base command for NIPT"""

import logging

import click

from cg.apps.nipt import NiptAPI
from cg.apps.hk import HousekeeperAPI
from cg.meta.upload.nipt import UploadNiptAPI

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def nipt(context):
    """Loading batches into the NIPT database"""

    click.echo(click.style("----------------- NIPT -----------------------"))

    context.obj["nipt_upload_api"] = UploadNiptAPI(
        nipt_api=NiptAPI(context.obj),
        hk_api=HousekeeperAPI(context.obj)
    )

@click.pass_context
def batches(context):
    """Loading batches into the NIPT database"""

    click.echo(click.style("----------------- BATCHES -----------------------"))

    context.obj["nipt_upload_api"].load_batches()
