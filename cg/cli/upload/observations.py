"""Code for uploading observations data via CLI"""
import logging
from typing import Optional

import click
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.loqus import LoqusdbAPI
from cg.constants import Pipeline
from cg.exc import DuplicateRecordError, DuplicateSampleError
from cg.meta.upload.observations import UploadObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store

from .utils import LinkHelper

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-c", "--case_id", help="internal case id, leave empty to process all")
@click.option("-l", "--case-limit", type=int, help="maximum number of cases to upload")
@click.option("--dry-run", is_flag=True, help="only print cases to be processed")
@click.pass_obj
def observations(
    context: CGConfig, case_id: Optional[str], case_limit: Optional[int], dry_run: bool
):
    """Upload observations from an analysis to LoqusDB."""

    click.echo(click.style("----------------- OBSERVATIONS ----------------"))
    status_db: Store = context.status_db
    housekeeper_api: HousekeeperAPI = context.housekeeper_api

    loqus_apis = {
        "wgs": LoqusdbAPI(context.dict()),
        "wes": LoqusdbAPI(context.dict(), analysis_type="wes"),
    }

    if case_id:
        families_to_upload = [status_db.family(case_id)]
    else:
        families_to_upload = status_db.observations_to_upload()

    nr_uploaded = 0
    for case_obj in families_to_upload:

        if case_limit is not None and nr_uploaded >= case_limit:
            LOG.info("Uploaded %d cases, observations upload will now stop", nr_uploaded)
            return

        if not case_obj.customer.loqus_upload:
            LOG.info(
                "%s: %s not whitelisted for upload to loqusdb. Skipping!",
                case_obj.internal_id,
                case_obj.customer.internal_id,
            )
            continue

        if case_obj.data_analysis.lower() != str(Pipeline.MIP_DNA):
            LOG.info("%s: has non-MIP data_analysis. Skipping!", case_obj.internal_id)
            continue

        if not LinkHelper.all_samples_are_non_tumour(case_obj.links):
            LOG.info("%s: has tumour samples. Skipping!", case_obj.internal_id)
            continue

        analysis_list = LinkHelper.get_analysis_type_for_each_link(case_obj.links)
        if len(set(analysis_list)) != 1 or analysis_list[0] not in (
            "wes",
            "wgs",
        ):
            LOG.info(
                "%s: Undetermined analysis type (wes or wgs) or mixed analyses. Skipping!",
                case_obj.internal_id,
            )
            continue

        analysis_type = analysis_list[0]

        if dry_run:
            LOG.info("%s: Would upload observations", case_obj.internal_id)
            continue

        upload_observations_api = UploadObservationsAPI(
            status_api=status_db, hk_api=housekeeper_api, loqus_api=loqus_apis[analysis_type]
        )

        try:
            upload_observations_api.process(case_obj.analyses[0])
            LOG.info("%s: observations uploaded!", case_obj.internal_id)
            nr_uploaded += 1
        except (DuplicateRecordError, DuplicateSampleError) as error:
            LOG.info("%s: skipping observations upload: %s", case_obj.internal_id, error.message)
        except FileNotFoundError as error:
            LOG.info("%s: skipping observations upload: %s", case_obj.internal_id, error)
