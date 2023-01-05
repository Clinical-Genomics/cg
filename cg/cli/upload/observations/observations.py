"""Code for uploading observations data via CLI."""

import contextlib
import logging
from datetime import datetime
from typing import Optional, Union

import click
from alchy import Query
from cgmodels.cg.constants import Pipeline
from pydantic import ValidationError

from cg.cli.upload.observations.utils import get_observations_case_to_upload, get_observations_api
from cg.exc import LoqusdbError, CaseNotFoundError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.store import models, Store

from cg.cli.workflow.commands import (
    ARGUMENT_CASE_ID,
    OPTION_DRY,
    OPTION_LOQUSDB_SUPPORTED_PIPELINES,
)
from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


@click.command("observations")
@ARGUMENT_CASE_ID
@OPTION_DRY
@click.pass_obj
def observations(context: CGConfig, case_id: Optional[str], dry_run: bool):
    """Upload observations from an analysis to Loqusdb."""

    click.echo(click.style("----------------- OBSERVATIONS -----------------"))

    with contextlib.suppress(LoqusdbError):
        case: models.Family = get_observations_case_to_upload(context, case_id)
        observations_api: Union[
            MipDNAObservationsAPI, BalsamicObservationsAPI
        ] = get_observations_api(context, case)

        if dry_run:
            LOG.info(f"Dry run. Would upload observations for {case.internal_id}.")
            return

        observations_api.upload(case)


@click.command("available-observations")
@OPTION_LOQUSDB_SUPPORTED_PIPELINES
@OPTION_DRY
@click.pass_context
def available_observations(context: click.Context, pipeline: Optional[Pipeline], dry_run: bool):
    """Uploads the available observations to Loqusdb."""

    click.echo(click.style("----------------- AVAILABLE OBSERVATIONS -----------------"))

    status_db: Store = context.obj.status_db
    cases_to_upload: Query = status_db.observations_to_upload(pipeline=pipeline)
    if not cases_to_upload:
        LOG.error(
            f"There are no available cases to upload to Loqusdb for {pipeline} ({datetime.now()})"
        )
        return

    for case in cases_to_upload:
        try:
            LOG.info(f"Will upload observations for {case.internal_id}")
            context.invoke(observations, case_id=case.internal_id, dry_run=dry_run)
        except (CaseNotFoundError, FileNotFoundError, ValidationError) as error:
            LOG.error(f"Error uploading observations for {case.internal_id}: {error}")
            continue
