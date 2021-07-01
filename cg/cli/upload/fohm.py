import logging

import click

from cg.meta.upload.fohm.fohm import FOHMUploadAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def fohm(context):
    pass


@fohm.command
@click.option("cases", "-c", multiple=True, type=str, required=True)
@click.pass_obj
def preprocess(context: CGConfig, cases: list):
    fohm_api = FOHMUploadAPI(context)
    fohm_api.assemble_fohm_delivery(cases=cases)


@fohm.command
@click.argument("date", type=str, required=False)
@click.pass_obj
def send_reports(context: CGConfig, date):
    fohm_api = FOHMUploadAPI(context)
    fohm_api.send_mail_reports(date)
