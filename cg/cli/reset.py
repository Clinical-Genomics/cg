import logging
from typing import Iterable, Optional

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.meta.upload.observations import UploadObservationsAPI
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
    """Delete case from LoqusDB and reset loqusdb_id in statusDB."""

    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api
    loqusdb_api: LoqusdbAPI = context.loqusdb_api

    observations_uploaded: Iterable[models.Family]

    if case_id:
        observations_uploaded = [status_db.family(case_id)]
    else:
        observations_uploaded = status_db.observations_uploaded()

    for case_obj in observations_uploaded:
        LOG.info("This would reset observation links for: %s", case_obj.internal_id)

    click.confirm("Do you want to continue?", abort=True)

    # Delete case from loqusDB
    if case_id:
        upload_observations_api = UploadObservationsAPI(
            status_api=status_db, hk_api=housekeeper_api, loqus_api=loqusdb_api
        )
        upload_observations_api.delete(case_obj.internal_id)
        LOG.info("Delete case %s from loqusDB", case_obj.internal_id)

    # Reset loqusdb_id in StatusDB
    for case_obj in observations_uploaded:
        status_db.reset_observations(case_obj.internal_id)
        LOG.info("Reset loqus observations for: %s", case_obj.internal_id)

    status_db.commit()
