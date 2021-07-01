import logging

import click

from cg.meta.upload.fohm.fohm import FOHMUploadAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.command()
@click.option("cases", "-c", multiple=True, type=str, required=True)
@click.pass_obj
def fohm(context: CGConfig, cases: list):
    fohm_api = FOHMUploadAPI(context)
    fohm_api.assemble_fohm_delivery(cases=cases)

    pass
