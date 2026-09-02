from typing import cast

from pydantic import BaseModel, Field

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.store.models import Case, Sample
from cg.store.store import Store


class ExternalSampleStoredEvent(BaseModel):
    sample_internal_id: str = Field(alias="status_db.sample_internal_id")


# TODO
"""
- IF a case can't start because it's waiting for external sample, acknowledge
- IF a case can't start because it's waiting for internal sample, set status to analyze
"""


"""
If purely external and everything -> start (do we need to set case to hold if purely external?)
Else: AK
"""


def _are_all_samples_external_and_stored(case: Case, housekeeper_api: HousekeeperAPI) -> bool:
    return all(
        sample.is_external
        and sample.case_that_delivers == case  # Ensures sample was originally ordered in this case
        and housekeeper_api.bundle(sample.internal_id)  # Ensures it has been stored
        for sample in case.samples
    )


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleStoredEvent.model_validate(event_payload)
    status_db: Store = config.status_db
    housekeeper_api: HousekeeperAPI = config.housekeeper_api

    sample: Sample = status_db.get_sample_by_internal_id_strict(event.sample_internal_id)
    case: Case = cast(Case, sample.case_that_delivers)
    if _are_all_samples_external_and_stored(case=case, housekeeper_api=housekeeper_api):
        # TODO: Check the samples had stored
        analysis_starter_factory = AnalysisStarterFactory(config)
        analysis_starter: AnalysisStarter = analysis_starter_factory.get_analysis_starter_for_case(
            case.internal_id
        )
        analysis_starter.start(case.internal_id)
    # From case get samples

    # For every sample check if external and if so if it has hk bundle

    # TODO: Start the case if previous check return true else return
    # TODO: If case fails to start raise error else just return
    pass
