"""Delete observations CLI."""

import logging
from typing import Optional, Union

import click
from sqlalchemy.orm import Query
from cgmodels.cg.constants import Pipeline

from cg.cli.upload.observations.utils import get_observations_api, get_observations_case
from cg.cli.workflow.commands import OPTION_LOQUSDB_SUPPORTED_PIPELINES, ARGUMENT_CASE_ID
from cg.exc import CaseNotFoundError, LoqusdbError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Family
from cg.constants.constants import DRY_RUN, SKIP_CONFIRMATION

LOG = logging.getLogger(__name__)


@click.command("observations")
@ARGUMENT_CASE_ID
@SKIP_CONFIRMATION
@DRY_RUN
@click.pass_obj
def delete_observations(context: CGConfig, case_id: str, dry_run: bool, yes: bool):
    """Delete a case from Loqusdb and reset the Loqusdb IDs in StatusDB."""

    case: Family = get_observations_case(context, case_id, upload=False)
    observations_api: Union[MipDNAObservationsAPI, BalsamicObservationsAPI] = get_observations_api(
        context, case
    )

    if dry_run:
        LOG.info(f"Dry run. This would delete all variants in Loqusdb for case: {case.internal_id}")
        return

    LOG.info(f"This will delete all variants in Loqusdb for case: {case.internal_id}")
    if yes or click.confirm("Do you want to continue?", abort=True):
        observations_api.delete_case(case)


@click.command("available-observations")
@OPTION_LOQUSDB_SUPPORTED_PIPELINES
@SKIP_CONFIRMATION
@DRY_RUN
@click.pass_context
def delete_available_observations(
    context: click.Context, pipeline: Optional[Pipeline], dry_run: bool, yes: bool
):
    """Delete available observation from Loqusdb."""

    status_db: Store = context.obj.status_db
    uploaded_observations: Query = status_db.observations_uploaded(pipeline)

    LOG.info(
        f"This would delete observations for the following cases: {[case.internal_id for case in uploaded_observations]}"
    )
    if yes or click.confirm("Do you want to continue?", abort=True):
        for case in uploaded_observations:
            try:
                LOG.info(f"Will delete observations for {case.internal_id}")
                context.invoke(
                    delete_observations,
                    case_id=case.internal_id,
                    dry_run=dry_run,
                    yes=yes,
                )
            except (CaseNotFoundError, LoqusdbError) as error:
                LOG.error(f"Error deleting observations for {case.internal_id}: {error}")
                continue
