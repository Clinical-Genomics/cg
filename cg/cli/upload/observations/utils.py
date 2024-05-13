"""Helper functions for observations related actions."""

import logging

from sqlalchemy.orm import Query

from cg.constants.constants import Workflow
from cg.constants.observations import LOQUSDB_SUPPORTED_WORKFLOWS
from cg.exc import CaseNotFoundError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def get_observations_verified_case(context: CGConfig, case_id: str | None, upload: bool) -> Case:
    """Return a verified Loqusdb case."""
    status_db: Store = context.status_db
    case: Case = status_db.get_case_by_internal_id(internal_id=case_id)
    if not case or case.data_analysis not in LOQUSDB_SUPPORTED_WORKFLOWS:
        LOG.error("Invalid case ID. Retrieving available cases for Loqusdb actions.")
        cases_to_process: Query = (
            status_db.observations_to_upload() if upload else status_db.observations_uploaded()
        )
        if not cases_to_process:
            LOG.info("There are no valid cases to be processed by Loqusdb")
        else:
            LOG.info("Provide one of the following case IDs: ")
            for case in cases_to_process:
                LOG.info(f"{case.internal_id} ({case.data_analysis})")
        raise CaseNotFoundError
    return case


def get_observations_api(
    context: CGConfig, case_id: str | None, upload: bool
) -> MipDNAObservationsAPI | BalsamicObservationsAPI:
    """Return an observations API given a specific case object."""
    case: Case = get_observations_verified_case(context=context, case_id=case_id, upload=upload)
    observations_apis = {
        Workflow.MIP_DNA: MipDNAObservationsAPI(context),
        Workflow.BALSAMIC: BalsamicObservationsAPI(context),
    }
    return observations_apis[case.data_analysis]
