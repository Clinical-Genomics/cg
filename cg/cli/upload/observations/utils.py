"""Helper functions for observations related actions."""

import logging

from sqlalchemy.orm import Query

from cg.constants.constants import Workflow
from cg.constants.observations import LOQUSDB_SUPPORTED_WORKFLOWS
from cg.constants.sequencing import SequencingMethod
from cg.exc import CaseNotFoundError, LoqusdbUploadCaseError
from cg.meta.observations.balsamic_observations_api import BalsamicObservationsAPI
from cg.meta.observations.mip_dna_observations_api import MipDNAObservationsAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def get_observations_case(context: CGConfig, case_id: str, upload: bool) -> Case:
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


def get_observations_case_to_upload(context: CGConfig, case_id: str) -> Case:
    """Return a verified case ready to be uploaded to Loqusdb."""
    case: Case = get_observations_case(context, case_id, upload=True)
    if not case.customer.loqus_upload:
        LOG.error(
            f"Customer {case.customer.internal_id} is not whitelisted for upload to Loqusdb. Canceling upload for "
            f"case {case.internal_id}."
        )
        raise LoqusdbUploadCaseError
    return case


def get_observations_api(
    context: CGConfig, case: Case
) -> MipDNAObservationsAPI | BalsamicObservationsAPI:
    """Return an observations API given a specific case object."""
    observations_apis = {
        Workflow.MIP_DNA: MipDNAObservationsAPI(context, get_sequencing_method(case)),
        Workflow.BALSAMIC: BalsamicObservationsAPI(context, get_sequencing_method(case)),
    }
    return observations_apis[case.data_analysis]


def get_sequencing_method(case: Case) -> SequencingMethod:
    """Returns the sequencing method for the given case object."""
    analysis_types = [
        link.sample.application_version.application.analysis_type for link in case.links
    ]
    if len(set(analysis_types)) != 1:
        LOG.error(f"Case {case.internal_id} has a mixed analysis type. Cancelling action.")
        raise LoqusdbUploadCaseError

    return analysis_types[0]
