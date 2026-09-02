from typing import cast

from pydantic import BaseModel, Field

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


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleStoredEvent.model_validate(event_payload)
    status_db: Store = config.status_db

    # TODO: Check if all external samples in the case are stored
    sample: Sample = status_db.get_sample_by_internal_id_strict(event.sample_internal_id)
    case: Case = cast(Case, sample.case_that_delivers)
    if all(sample.is_external and sample.case_that_delivers == case for sample in case.samples):
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
