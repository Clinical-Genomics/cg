import logging

from alchy import Query

from cg.apps.loqus import LoqusdbAPI
from cg.cli.upload.utils import LinkHelper
from cg.constants.observations import LOQUSDB_SUPPORTED_PIPELINES
from cg.exc import CaseNotFoundError, LoqusdbUploadError
from cg.meta.upload.observations.observations_api import UploadObservationsAPI
from cg.store import models

from cg.models.cg_config import CGConfig


LOG = logging.getLogger(__name__)


def get_observations_case(context: CGConfig, case_id: str) -> models.Family:
    """Return a verified Loqusdb case."""

    case: models.Family = context.status_db.family(case_id)
    if not case or case.data_analysis not in LOQUSDB_SUPPORTED_PIPELINES:
        LOG.error("Invalid case ID. Retrieving available cases for Loqusdb actions.")
        cases_to_upload: Query = context.status_db.observations_to_upload()
        if not cases_to_upload:
            LOG.info("There are no valid cases to be processed by Loqusdb")
        else:
            LOG.info("Provide one of the following case IDs: ")
            for case in cases_to_upload:
                LOG.info(f"{case.internal_id} ({case.data_analysis})")

        raise CaseNotFoundError

    return case


def get_observations_case_to_upload(context: CGConfig, case_id: str) -> models.Family:
    """Return a verified case ready to be uploaded to LoqusDB."""

    case: models.Family = get_observations_case(context, case_id)
    if not case.customer.loqus_upload:
        LOG.error(
            f"Customer {case.customer.internal_id} is not whitelisted for upload to Loqusdb. Canceling upload for "
            f"case {case.internal_id}."
        )
        raise LoqusdbUploadError

    if not LinkHelper.is_all_samples_non_tumour(case.links):
        LOG.error(f"Case {case.internal_id} has tumor samples. Cancelling its upload.")
        raise LoqusdbUploadError

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
        raise LoqusdbUploadError

    analysis_type = analysis_list[0]
    return UploadObservationsAPI(
        status_api=context.status_db,
        hk_api=context.housekeeper_api,
        loqus_api=loqus_apis[analysis_type],
    )
