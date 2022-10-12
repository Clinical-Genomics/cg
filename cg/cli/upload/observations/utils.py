import logging
from typing import Dict, List

from alchy import Query

from cg.apps.loqus import LoqusdbAPI
from cg.constants.observations import LOQUSDB_SUPPORTED_PIPELINES
from cg.constants.sequencing import SequencingMethod
from cg.exc import CaseNotFoundError, CustomerPermissionError, DataIntegrityError
from cg.meta.upload.observations.observations_api import UploadObservationsAPI
from cg.store import models, Store

from cg.models.cg_config import CGConfig
from cg.store.api.link import LinkHelper

LOG = logging.getLogger(__name__)


def get_observations_case(context: CGConfig, case_id: str, upload: bool) -> models.Family:
    """Return a verified Loqusdb case."""

    status_db: Store = context.status_db
    case: models.Family = status_db.family(case_id)
    if not case or case.data_analysis not in LOQUSDB_SUPPORTED_PIPELINES:
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


def get_observations_case_to_upload(context: CGConfig, case_id: str) -> models.Family:
    """Return a verified case ready to be uploaded to Loqusdb."""

    case: models.Family = get_observations_case(context, case_id, upload=True)
    if not case.customer.loqus_upload:
        LOG.error(
            f"Customer {case.customer.internal_id} is not whitelisted for upload to Loqusdb. Canceling upload for "
            f"case {case.internal_id}."
        )
        raise CustomerPermissionError

    if not LinkHelper.is_all_samples_non_tumour(case.links):
        LOG.error(f"Case {case.internal_id} has tumor samples. Cancelling its upload.")
        raise DataIntegrityError
    return case


def get_observations_case_to_delete(context: CGConfig, case_id: str) -> models.Family:
    """Return a verified case ready to be deleted from Loqusdb."""

    loqusdb_api: LoqusdbAPI = context.loqusdb_api
    case: models.Family = get_observations_case(context, case_id, upload=False)
    if not loqusdb_api.case_exists(case_id):
        LOG.error(
            f"Case {case.internal_id} could not be found in Loqusdb",
        )
        raise CaseNotFoundError
    return case


def get_observations_api(context: CGConfig, case: models.Family) -> UploadObservationsAPI:
    """Return an observations API given a specific case object."""

    loqus_apis: Dict[SequencingMethod, LoqusdbAPI] = {
        SequencingMethod.WGS: LoqusdbAPI(context.dict()),
        SequencingMethod.WES: LoqusdbAPI(context.dict(), analysis_type=SequencingMethod.WES),
    }

    analysis_types: List[SequencingMethod] = LinkHelper.get_analysis_type_for_each_link(case.links)
    if len(set(analysis_types)) != 1 or analysis_types[0] not in (
        SequencingMethod.WES,
        SequencingMethod.WGS,
    ):
        LOG.error(
            f"Case {case.internal_id} has an undetermined analysis type or mixed analyses. Cancelling its upload."
        )
        raise DataIntegrityError

    analysis_type: SequencingMethod = analysis_types[0]
    return UploadObservationsAPI(
        status_api=context.status_db,
        hk_api=context.housekeeper_api,
        loqus_api=loqus_apis[analysis_type],
    )
