"""Code for uploading genotype data via CLI"""
import logging

import click

from cg.exc import CgError
from cg.meta.upload.gisaid import GisaidAPI
from cg.models.cg_config import CGConfig
from cg.models.email import EmailInfo
from cg.utils.email import send_mail

LOG = logging.getLogger(__name__)


@click.command()
@click.argument("case_id", required=True)
@click.pass_obj
def gisaid(context: CGConfig, case_id: str):
    """Upload mutant analysis data to GISAID."""

    LOG.info("----------------- GISAID UPLOAD -------------------")

    gisaid_api = GisaidAPI(config=context)

    try:
        gisaid_api.upload(case_id=case_id)
        LOG.info("Upload to GISAID successful")
    except CgError as error:
        email_info: EmailInfo = EmailInfo(
            **gisaid_api.email_base_settings.dict(),
            receiver_email=gisaid_api.log_watch,
            message=error.message,
            subject="Gisaid Upload Failed",
        )
        send_mail(email_info)
        LOG.error("Upload Failed")
        raise
