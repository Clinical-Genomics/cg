""" Upload NIPT results via the CLI"""

import logging
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

    click.echo(click.style("NIPT UPLOAD START"))

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
        message = f"Analysis already uploaded: {analysis_obj.uploaded_at.date()}"
        click.echo(click.style(message, fg="yellow"))
    else:
        analysis_obj.upload_started_at = datetime.now()
        status_db.commit()
        context.invoke(batch, case_id=case_id)
        context.invoke(nipt_upload_case, case_id=case_id)
        analysis_obj.uploaded_at = datetime.now()
        status_db.commit()
        click.echo(click.style(f"{case_id}: analysis uploaded!", fg="green"))


nipt.add_command(ftp)
nipt.add_command(statina)

