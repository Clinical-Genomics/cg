import logging
from typing import Iterable, Optional

import click
from alchy import Query
from cgmodels.cg.constants import Pipeline

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.constants.observations import LOQUSDB_SUPPORTED_PIPELINES
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group("reset")
def reset_cmd():
    """Reset information in the database."""
    pass


@reset_cmd.command()
@ARGUMENT_CASE_ID
@click.pass_obj
def observations(context: CGConfig, case_id: str):
    """Reset observation links from an analysis to Loqusdb for a specific case."""

    status_db: Store = context.status_db
    case: models.Family = context.status_db.family(case_id)

    if not case or case.data_analysis not in LOQUSDB_SUPPORTED_PIPELINES:
        LOG.error("Invalid case ID. Retrieving available cases for Loqusdb reset.")
        uploaded_observations: Query = status_db.observations_uploaded()
        if not uploaded_observations:
            LOG.info("There are no available case uploaded observations")
        else:
            LOG.info("Provide one of the following case IDs: ")
            for case in uploaded_observations:
                LOG.info(f"{case.internal_id} ({case.data_analysis})")
        raise click.Abort()

    status_db.reset_observations(case)
    status_db.commit()
    LOG.info(f"Reset Loqusdb observations for {case.internal_id}")


@reset_cmd.command()
@click.option(
    "--pipeline",
    type=click.Choice(LOQUSDB_SUPPORTED_PIPELINES),
    help="Limit observations reset to a specific pipeline",
)
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
        context.invoke(observations, case_id=case.internal_id)
