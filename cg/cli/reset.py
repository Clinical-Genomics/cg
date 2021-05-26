import logging
from typing import Iterable, Optional

import click
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group("reset")
def reset_cmd():
    """Reset information in the database."""
    pass


@reset_cmd.command()
@click.option("-c", "--case_id", help="internal case id, leave empty to process all")
@click.pass_obj
def observations(context: CGConfig, case_id: Optional[str]):
    """Reset observation links from an analysis to LoqusDB."""
    status_db: Store = context.status_db
    observations_uploaded: Iterable[models.Family]
    if case_id:
        observations_uploaded = [status_db.family(case_id)]
    else:
        observations_uploaded = status_db.observations_uploaded()

    for case_obj in observations_uploaded:
        LOG.info("This would reset observation links for: %s", case_obj.internal_id)

    click.confirm("Do you want to continue?", abort=True)

    for case_obj in observations_uploaded:
        status_db.reset_observations(case_obj.internal_id)
        LOG.info("Reset loqus observations for: %s", case_obj.internal_id)

    status_db.commit()
