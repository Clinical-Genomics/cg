import logging

import click
from cg.apps.loqus import LoqusdbAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group("delete")
def delete_cmd():
    """Delete variants associated to a case in LoqusDB."""
    pass


@delete_cmd.command()
@click.option("-c", "--case_id", help="internal case id")
@click.pass_obj
def observations(context: CGConfig, case_id: str):
    """Delete case from LoqusDB and reset loqusdb_id in statusDB."""

    status_db: Store = context.status_db
    loqusdb_api: LoqusdbAPI = context.loqusdb_api

    # Make sure case exist before attempting to delete it
    loqusdb_api.get_case(case_id=case_id)

    # Delete case from loqusdb
    LOG.info("This will delete all variants in LoqusDB for case: %s", case_id)
    click.confirm("Do you want to continue?", abort=True)
    LOG.info("Delete variants from LoqusDB for case: %s", case_id)
    loqusdb_api.delete(case_id=case_id)

    # If a case is deleted reset StatusDB loqusdb_id to None
    status_db.reset_observations(case_id)
    LOG.info("Reset loqus_id in StatusDB for: %s", case_id)
    status_db.commit()
