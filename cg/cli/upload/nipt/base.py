""" Upload NIPT results via the CLI"""

import logging
import sys
import traceback
from datetime import datetime
from typing import Optional

from cg.cli.upload.utils import suggest_cases_to_upload
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from cgmodels.cg.constants import Pipeline

from .ftp import ftp, nipt_upload_case
from .statina import statina, batch

import click

LOG = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("-c", "--case", "case_id", help="Upload to all apps")
@click.pass_context
def nipt(context: click.Context, case_id: Optional[str]):
    """Upload NIPT result files"""

    LOG.info("*** NIPT UPLOAD START ***")

    if context.invoked_subcommand is not None:
        return

    config_object: CGConfig = context.obj
    status_db: Store = config_object.status_db

    if not case_id:
        suggest_cases_to_upload(status_db=status_db, pipeline=Pipeline.FLUFFY)
        raise click.Abort

    case_obj: models.Family = status_db.family(case_id)
    analysis_obj: models.Analysis = case_obj.analyses[0]

    if analysis_obj.uploaded_at is not None:
        LOG.warning("Analysis already uploaded: %s", analysis_obj.uploaded_at.date())
    else:
        analysis_obj.upload_started_at = datetime.now()
        status_db.commit()
        context.invoke(batch, case_id=case_id)
        context.invoke(nipt_upload_case, case_id=case_id)
        analysis_obj.uploaded_at = datetime.now()
        status_db.commit()
        LOG.info("%s: analysis uploaded!", case_id)


@nipt.command()
@click.pass_context
def auto(context: click.Context):
    """Upload all NIPT result files"""

    LOG.info("*** NIPT UPLOAD ALL START ***")

    status_db: Store = context.obj.status_db

    exit_code = 0
    for analysis_obj in status_db.analyses_to_upload(pipeline=Pipeline.FLUFFY):

        if analysis_obj.family.analyses[0].uploaded_at is not None:
            LOG.warning(
                "More recent analysis already uploaded for %s, skipping",
                analysis_obj.family.internal_id,
            )
            continue
        internal_id = analysis_obj.family.internal_id

        LOG.info("Uploading case: %s", internal_id)
        try:
            context.invoke(nipt, case_id=internal_id)
        except Exception:
            LOG.error("Uploading case failed: %s", internal_id)
            LOG.error(traceback.format_exc())
            exit_code = 1

    sys.exit(exit_code)


nipt.add_command(ftp)
nipt.add_command(statina)
