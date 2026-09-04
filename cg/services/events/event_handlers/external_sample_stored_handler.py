from pydantic import BaseModel, Field

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import CaseNotFoundError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.store.models import Case, Sample
from cg.store.store import Store


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
        analysis_starter_factory = AnalysisStarterFactory(config)
        analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_case(
            case.internal_id
        )
        analysis_starter.start(case.internal_id)


def _are_all_samples_new_external_and_stored(case: Case, housekeeper_api: HousekeeperAPI) -> bool:
    """
    Return True if all of the samples of the case are external, stored in Housekeeper
    and are originally ordered with the case.
    """
    return all(
        sample.is_external
        and sample.case_that_delivers == case  # Ensures sample was originally ordered in this case
        and housekeeper_api.bundle(sample.internal_id)  # Ensures it has been stored
        for sample in case.samples
    )
