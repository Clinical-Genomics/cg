import logging

import click
from cg.apps.loqus import LoqusdbAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from cg.constants.constants import DRY_RUN, SKIP_CONFIRMATION

LOG = logging.getLogger(__name__)


@click.group("delete")
def delete_cmd():
    """Delete variants associated to a case in LoqusDB."""
    pass


@delete_cmd.command()
@click.option("-c", "--case_id", help="internal case id")
@DRY_RUN
@SKIP_CONFIRMATION
@click.pass_obj
def observations(context: CGConfig, case_id: str, dry_run: bool, yes: bool):
    """Delete case from LoqusDB and reset loqusdb_id in statusDB."""

    status_db: Store = context.status_db
    loqusdb_api: LoqusdbAPI = context.loqusdb_api

    if dry_run:
        LOG.info("DRY-RUN MODE. Variants will not be deleted.")
        LOG.info("This would delete all variants in LoqusDB for case: %s", case_id)

    else:
        LOG.info("This will delete all variants in LoqusDB for case: %s", case_id)

        if yes or click.confirm("Do you want to continue?", abort=True):
            LOG.info("Delete variants from LoqusDB for case: %s", case_id)
            loqusdb_api.delete_case(case_id=case_id)

            LOG.info("Reset loqus_id in StatusDB for: %s", case_id)
            status_db.reset_loqusdb_observation_ids(case_id)
            status_db.commit()
