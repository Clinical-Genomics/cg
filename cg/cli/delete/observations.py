import logging

import click
from cg.apps.loqus import LoqusdbAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.constants.constants import DRY_RUN, SKIP_CONFIRMATION

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-c", "--case_id", required=True, help="internal case id")
@DRY_RUN
@SKIP_CONFIRMATION
@click.pass_obj
def observations(context: CGConfig, case_id: str, dry_run: bool, yes: bool):
    """Delete a case from LoqusDB and reset loqusdb_id in statusDB."""

    status_db: Store = context.status_db
    loqusdb_api: LoqusdbAPI = context.loqusdb_api

    if not status_db.family(case_id):
        LOG.error("Case %s could not be found in StatusDB!", case_id)
        raise click.Abort

    if not loqusdb_api.case_exists(case_id):
        LOG.error("Case %s could not be found in LoqusDB!", case_id)
        raise click.Abort

    if dry_run:
        LOG.info("Dry run: this would delete all variants in LoqusDB for case: %s", case_id)
        return

    LOG.info("This will delete all variants in LoqusDB for case: %s", case_id)

    if yes or click.confirm("Do you want to continue?", abort=True):
        LOG.info("Deleting variants from LoqusDB for case: %s", case_id)
        loqusdb_api.delete_case(case_id=case_id)
        status_db.reset_loqusdb_observation_ids(case_id)
        status_db.commit()
        LOG.info("Removed observations for case: %s", case_id)
