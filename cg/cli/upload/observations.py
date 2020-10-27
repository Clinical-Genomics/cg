"""Code for uploading observations data via CLI"""
import logging

import click

from cg.apps.loqus import LoqusdbAPI
from cg.exc import DuplicateRecordError, DuplicateSampleError
from cg.meta.upload.observations import UploadObservationsAPI

from .utils import LinkHelper

LOG = logging.getLogger(__name__)


@click.command()
@click.option("-c", "--case_id", help="internal case id, leave empty to process all")
@click.option("-l", "--case-limit", type=int, help="maximum number of cases to upload")
@click.option("--dry-run", is_flag=True, help="only print cases to be processed")
@click.pass_context
def observations(context, case_id, case_limit, dry_run):
    """Upload observations from an analysis to LoqusDB."""

    click.echo(click.style("----------------- OBSERVATIONS ----------------"))

    loqus_apis = {
        "wgs": LoqusdbAPI(context.obj),
        "wes": LoqusdbAPI(context.obj, analysis_type="wes"),
    }
    status_api = context.obj["status_db"]
    hk_api = context.obj["housekeeper_api"]

    if case_id:
        families_to_upload = [status_api.family(case_id)]
    else:
        families_to_upload = status_api.observations_to_upload()

    nr_uploaded = 0
    for family_obj in families_to_upload:

        if case_limit is not None:
            if nr_uploaded >= case_limit:
                LOG.info("Uploaded %d cases, observations upload will now stop", nr_uploaded)
                return

        if not family_obj.customer.loqus_upload:
            LOG.info(
                "%s: %s not whitelisted for upload to loqusdb. Skipping!",
                family_obj.internal_id,
                family_obj.customer.internal_id,
            )
            continue

        if family_obj.data_analysis.lower() != "mip":
            LOG.info("%s: has non-MIP data_analysis. Skipping!", family_obj.internal_id)
            continue

        if not LinkHelper.all_samples_are_non_tumour(family_obj.links):
            LOG.info("%s: has tumour samples. Skipping!", family_obj.internal_id)
            continue

        analysis_list = LinkHelper.get_analysis_type_for_each_link(family_obj.links)
        if not (len(set(analysis_list)) == 1 and analysis_list[0] in ("wes", "wgs")):
            LOG.info(
                "%s: Undetermined analysis type (wes or wgs) or mixed analyses. Skipping!",
                family_obj.internal_id,
            )
            continue

        analysis_type = analysis_list[0]

        if dry_run:
            LOG.info("%s: Would upload observations", family_obj.internal_id)
            continue

        api = UploadObservationsAPI(status_api, hk_api, loqus_apis[analysis_type])

        try:
            api.process(family_obj.analyses[0])
            LOG.info("%s: observations uploaded!", family_obj.internal_id)
            nr_uploaded += 1
        except (DuplicateRecordError, DuplicateSampleError) as error:
            LOG.info("%s: skipping observations upload: %s", family_obj.internal_id, error.message)
        except FileNotFoundError as error:
            LOG.info("%s: skipping observations upload: %s", family_obj.internal_id, error)
