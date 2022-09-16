"""Code for uploading observations data via CLI"""

import logging
from datetime import datetime
from typing import Optional

import click
from alchy import Query
from cgmodels.cg.constants import Pipeline

from cg.apps.loqus import LoqusdbAPI
from cg.cli.upload.utils import LinkHelper
from cg.constants.observations import LOQUSDB_SUPPORTED_PIPELINES
from cg.exc import DuplicateRecordError, DuplicateSampleError
from cg.meta.upload.observations import UploadObservationsAPI
from cg.store import models, Store

from cg.cli.workflow.commands import ARGUMENT_CASE_ID
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@click.command("observations")
@ARGUMENT_CASE_ID
@click.option("--dry-run", is_flag=True, help="Only prints the existing case to be processed")
@click.pass_obj
def observations(context: CGConfig, case_id: Optional[str], dry_run: bool):
    """Upload observations from an analysis to Loqusdb."""

    click.echo(click.style("----------------- OBSERVATIONS -----------------"))

    case: models.Family = get_observations_case(context, case_id)
    observations_api: UploadObservationsAPI = get_observations_api(context, case)

    if dry_run:
        LOG.info(f"Dry run. Would upload observations for {case.internal_id}.")
        return

    try:
        observations_api.process(case.analyses[0])
    except (FileNotFoundError, DuplicateRecordError, DuplicateSampleError) as error:
        LOG.error(f"Cancelling observations upload for case {case.internal_id}, {error.message}")
        return

    LOG.info(f"Observations uploaded for case: {case.internal_id}")


@click.command("available-observations")
@click.option(
    "--pipeline",
    type=click.Choice(LOQUSDB_SUPPORTED_PIPELINES),
    help="Limit observations upload to a specific pipeline",
)
@click.option("--dry-run", is_flag=True, help="Only print the cases that would be processed")
@click.pass_context
def available_observations(context: click.Context, pipeline: Optional[Pipeline], dry_run: bool):
    """Uploads the available observations to Loqusdb."""

    click.echo(click.style("----------------- AVAILABLE OBSERVATIONS -----------------"))

    status_db: Store = context.obj.status_db
    cases_to_upload: Query = status_db.observations_to_upload(pipeline=pipeline)
    if not cases_to_upload:
        LOG.error(
            f"There are no available cases to upload to Loqusdb for {pipeline} ({datetime.now()})"
        )
        return

    for case in cases_to_upload:
        context.invoke(observations, case=case.internal_id, dry_run=dry_run)


def get_observations_case(context: CGConfig, case_id: str) -> models.Family:
    """Return a valid Loqusdb case to upload given a case ID."""

    case: models.Family = context.status_db.family(case_id)
    if not case or case.data_analysis not in LOQUSDB_SUPPORTED_PIPELINES:
        LOG.error("Invalid case ID. Retrieving available cases for Loqusdb upload.")
        cases_to_upload: Query = context.status_db.observations_to_upload()
        if not cases_to_upload:
            LOG.info("There are no valid cases to upload to Loqusdb")
        else:
            LOG.info("Provide one of the following case IDs: ")
            for case in cases_to_upload:
                LOG.info(f"{case.internal_id} ({case.data_analysis})")
        raise click.Abort()
    elif not case.customer.loqus_upload:
        LOG.error(
            f"Customer {case.customer.internal_id} is not whitelisted for upload to Loqusdb. Canceling upload for "
            f"case {case.internal_id}."
        )
        raise click.Abort()
    elif not LinkHelper.all_samples_are_non_tumour(case.links):
        LOG.error(f"Case {case.internal_id} has tumor samples. Cancelling its upload.")
        raise click.Abort()

    return case


def get_observations_api(context: CGConfig, case: models.Family) -> UploadObservationsAPI:
    """Return an observations API given a specific case object."""

    loqus_apis = {
        "wgs": LoqusdbAPI(context.dict()),
        "wes": LoqusdbAPI(context.dict(), analysis_type="wes"),
    }

    analysis_list = LinkHelper.get_analysis_type_for_each_link(case.links)
    if len(set(analysis_list)) != 1 or analysis_list[0] not in ("wes", "wgs"):
        LOG.error(
            f"Case {case.internal_id} has an undetermined analysis type or mixed analyses. Cancelling its upload."
        )
        raise click.Abort()

    analysis_type = analysis_list[0]
    upload_observations_api = UploadObservationsAPI(
        status_api=context.status_db,
        hk_api=context.housekeeper_api,
        loqus_api=loqus_apis[analysis_type],
    )

    return upload_observations_api
