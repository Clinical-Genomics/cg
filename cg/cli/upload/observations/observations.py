"""Code for uploading observations data via CLI."""

import contextlib
import logging
from datetime import datetime

import click
from pydantic.v1 import ValidationError
from sqlalchemy.orm import Query

from cg.cli.upload.observations.utils import (
    get_observations_api,
    get_observations_case_to_upload,
)
from cg.cli.workflow.commands import (
    ARGUMENT_CASE_ID,
    OPTION_DRY,
    OPTION_LOQUSDB_SUPPORTED_WORKFLOW,
)
from cg.constants.constants import Workflow
from cg.exc import CaseNotFoundError, LoqusdbError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("observations")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def upload_observations_to_loqusdb(context: CGConfig, case_id: str | None, dry_run: bool):
    """Upload observations from an analysis to Loqusdb."""

    click.echo(click.style("----------------- OBSERVATIONS -----------------"))

    with contextlib.suppress(LoqusdbError):
        case: Case = get_observations_case_to_upload(context, case_id)
        observations_api: MipDNAObservationsAPI | BalsamicObservationsAPI = get_observations_api(
            context, case
        )

        if dry_run:
            LOG.info(f"Dry run. Would upload observations for {case.internal_id}.")
            return

        observations_api.upload(case)


@click.command("available-observations")
@OPTION_LOQUSDB_SUPPORTED_WORKFLOW
@OPTION_DRY
@click.pass_context
def upload_available_observations_to_loqusdb(
    context: click.Context, workflow: Workflow | None, dry_run: bool
):
    """Uploads the available observations to Loqusdb."""

    click.echo(click.style("----------------- AVAILABLE OBSERVATIONS -----------------"))

    status_db: Store = context.obj.status_db
    cases_to_upload: Query = status_db.observations_to_upload(workflow=workflow)
    if not cases_to_upload:
        LOG.error(
            f"There are no available cases to upload to Loqusdb for {workflow} ({datetime.now()})"
        )
        return

    for case in cases_to_upload:
        try:
            LOG.info(f"Will upload observations for {case.internal_id}")
            context.invoke(
                upload_observations_to_loqusdb, case_id=case.internal_id, dry_run=dry_run
            )
        except (CaseNotFoundError, FileNotFoundError, ValidationError) as error:
            LOG.error(f"Error uploading observations for {case.internal_id}: {error}")
            continue
