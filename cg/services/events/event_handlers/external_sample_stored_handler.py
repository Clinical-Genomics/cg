import logging

from pydantic import BaseModel, Field

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import CaseNotFoundError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.store.models import Case, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class ExternalSampleStoredEvent(BaseModel):
    sample_internal_id: str = Field(alias="status_db.sample_internal_id")


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleStoredEvent.model_validate(event_payload)
    status_db: Store = config.status_db
    housekeeper_api: HousekeeperAPI = config.housekeeper_api

    sample: Sample = status_db.get_sample_by_internal_id_strict(event.sample_internal_id)
    case: Case | None = sample.case_that_delivers
    if not case:
        raise CaseNotFoundError(f"No case found to deliver sample {sample.internal_id}")
    if _are_all_samples_new_external_and_stored(case=case, housekeeper_api=housekeeper_api):
        LOG.info(f"Case {case.internal_id} is ready to be started.")
        analysis_starter_factory = AnalysisStarterFactory(config)
        analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_case(
            case.internal_id
        )
        analysis_starter.start(case.internal_id)
    else:
        LOG.info(f"Case {case.internal_id} is not ready to be started.")


def _are_all_samples_new_external_and_stored(case: Case, housekeeper_api: HousekeeperAPI) -> bool:
    """
    Return True if all of the samples of the case are external, stored in Housekeeper
    and are originally ordered with the case.
    """
    not_external: list[str] = []
    not_new: list[str] = []
    not_stored: list[str] = []
    for sample in case.samples:
        if not sample.is_external:
            not_external.append(sample.internal_id)
        if not sample.case_that_delivers == case:
            not_new.append(sample.internal_id)
        if not housekeeper_api.bundle(sample.internal_id):
            not_stored.append(sample.internal_id)
    if any([not_external, not_new, not_stored]):
        LOG.info(
            f"Could not start analysis because of the following samples:\n"
            + f"Not external: {not_external}\n"
            if not_external
            else (
                "" + f"Not new: {not_new}\n"
                if not_new
                else "" + f"Not stored: {not_stored}" if not_stored else ""
            )
        )

    """return all(
        sample.is_external
        and sample.case_that_delivers == case  # Ensures sample was originally ordered in this case
        and housekeeper_api.bundle(sample.internal_id)  # Ensures it has been stored
        for sample in case.samples
    )"""
