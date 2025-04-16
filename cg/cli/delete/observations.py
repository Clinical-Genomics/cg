"""Delete observations CLI."""

import logging

import rich_click as click
from sqlalchemy.orm import Query

from cg.cli.upload.observations.utils import get_observations_api
from cg.cli.workflow.commands import ARGUMENT_CASE_ID, OPTION_LOQUSDB_SUPPORTED_WORKFLOW
from cg.constants.cli_options import DRY_RUN, SKIP_CONFIRMATION
from cg.constants.constants import Workflow
from cg.exc import CaseNotFoundError, LoqusdbError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.meta.observations.nallo_observations_api import NalloObservationsAPI
from cg.meta.observations.raredisease_observations_api import RarediseaseObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.command("observations")
@ARGUMENT_CASE_ID
@SKIP_CONFIRMATION
@DRY_RUN
@click.pass_obj
def delete_observations(context: CGConfig, case_id: str, dry_run: bool, skip_confirmation: bool):
    """Delete a case from Loqusdb and reset the Loqusdb IDs in StatusDB."""
    observations_api: (
        BalsamicObservationsAPI
        | MipDNAObservationsAPI
        | NalloObservationsAPI
        | RarediseaseObservationsAPI
    ) = get_observations_api(context=context, case_id=case_id, upload=False)
    if dry_run:
        LOG.info(f"Dry run. This would delete all variants in Loqusdb for case: {case_id}")
        return
    LOG.info(f"This will delete all variants in Loqusdb for case: {case_id}")
    if skip_confirmation or click.confirm("Do you want to continue?", abort=True):
        observations_api.delete_case(case_id)


@click.command("available-observations")
@OPTION_LOQUSDB_SUPPORTED_WORKFLOW
@SKIP_CONFIRMATION
@DRY_RUN
@click.pass_context
def delete_available_observations(
    context: click.Context, workflow: Workflow | None, dry_run: bool, skip_confirmation: bool
):
    """Delete available observation from Loqusdb."""
    status_db: Store = context.obj.status_db
    uploaded_observations: Query = status_db.observations_uploaded(workflow)
    LOG.info(
        f"This would delete observations for the following cases: "
        f"{[case.internal_id for case in uploaded_observations]}"
    )
    if skip_confirmation or click.confirm("Do you want to continue?", abort=True):
        for case in uploaded_observations:
            try:
                LOG.info(f"Will delete observations for {case.internal_id}")
                context.invoke(
                    delete_observations,
                    case_id=case.internal_id,
                    dry_run=dry_run,
                    skip_confirmation=skip_confirmation,
                )
            except (CaseNotFoundError, LoqusdbError) as error:
                LOG.error(f"Error deleting observations for {case.internal_id}: {error}")
                continue
