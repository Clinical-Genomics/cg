"""Delete observations CLI."""

import logging
from typing import Optional

import click
from alchy import Query
from cgmodels.cg.constants import Pipeline

from cg.cli.upload.observations.utils import get_observations_case_to_delete, get_observations_api
from cg.cli.workflow.commands import OPTION_LOQUSDB_SUPPORTED_PIPELINES, ARGUMENT_CASE_ID
from cg.exc import CaseNotFoundError, LoqusdbError
from cg.meta.observations.observations_api import ObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from cg.constants.constants import DRY_RUN, SKIP_CONFIRMATION

LOG = logging.getLogger(__name__)


@click.command()
@ARGUMENT_CASE_ID
@SKIP_CONFIRMATION
@DRY_RUN
@click.pass_obj
def observations(context: CGConfig, case_id: str, yes: bool, dry_run: bool):
    """Delete a case from Loqusdb and reset the Loqusdb IDs in StatusDB."""

    case: models.Family = get_observations_case_to_delete(context, case_id)
    observations_api: ObservationsAPI = get_observations_api(context, case)

    if dry_run:
        LOG.info(f"Dry run. This would delete all variants in Loqusdb for case: {case.internal_id}")
        return

    LOG.info(f"This will delete all variants in Loqusdb for case: {case.internal_id}")
    if yes or click.confirm("Do you want to continue?", abort=True):
        observations_api.delete_case(case)


@click.command("available-observations")
@OPTION_LOQUSDB_SUPPORTED_PIPELINES
@SKIP_CONFIRMATION
@DRY_RUN
@click.pass_context
def available_observations(
    context: click.Context, pipeline: Optional[Pipeline], yes: bool, dry_run: bool
):
    """Delete available observation from Loqusdb."""

    status_db: Store = context.obj.status_db
    uploaded_observations: Query = status_db.observations_uploaded(pipeline)

    LOG.info(
        f"This would delete observations for the following cases: {[case.internal_id for case in uploaded_observations]}"
    )
    if yes or click.confirm("Do you want to continue?", abort=True):
        for case in uploaded_observations:
            try:
                context.invoke(observations, case_id=case.internal_id, yes=yes, dry_run=dry_run)
            except (CaseNotFoundError, LoqusdbError):
                continue
