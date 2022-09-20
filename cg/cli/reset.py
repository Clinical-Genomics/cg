import logging
from typing import Optional

import click
from alchy import Query
from cgmodels.cg.constants import Pipeline

from cg.cli.upload.observations.utils import get_observations_case
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, OPTION_LOQUSDB_SUPPORTED_PIPELINES
from cg.exc import CaseNotFoundError
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group("reset")
def reset_cmd():
    """Reset information in the database."""
    pass


@reset_cmd.command("observations")
@ARGUMENT_CASE_ID
@click.pass_obj
def observations(context: CGConfig, case_id: str):
    """Reset observation links from an analysis to Loqusdb for a specific case."""

    status_db: Store = context.status_db
    case: models.Family = get_observations_case(context, case_id)

    status_db.reset_observations(case)
    status_db.commit()
    LOG.info(f"Reset Loqusdb observations for {case.internal_id}")


@reset_cmd.command("available-observations")
@OPTION_LOQUSDB_SUPPORTED_PIPELINES
@click.pass_context
def available_observations(context: click.Context, pipeline: Optional[Pipeline]):
    """Reset available observation links from an analysis to Loqusdb."""

    status_db: Store = context.obj.status_db
    uploaded_observations: Query = status_db.observations_uploaded(pipeline)

    LOG.info(
        f"This would reset observation links for {[case.internal_id for case in uploaded_observations]}"
    )
    click.confirm("Do you want to continue?", abort=True)

    for case in uploaded_observations:
        try:
            context.invoke(observations, case_id=case.internal_id)
        except CaseNotFoundError:
            continue
