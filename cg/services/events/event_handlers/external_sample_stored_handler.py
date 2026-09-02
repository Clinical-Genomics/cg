from pydantic import BaseModel, Field

from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store


class ExternalSampleStoredEvent(BaseModel):
    sample_internal_id: str = Field(alias="status_db.sample_internal_id")


# TODO
"""
- IF a case can't start because it's waiting for external sample, acknowledge
- IF a case can't start because it's waiting for internal sample, set status to analyze
"""


def handle(config: CGConfig, event_payload: dict) -> None:
    event = ExternalSampleStoredEvent.model_validate(event_payload)
    status_db: Store = config.status_db

    # TODO: Check if all external samples in the case are stored
    sample: Sample = status_db.get_sample_by_internal_id_strict(event.sample_internal_id)
    case: Case | None = sample.case_that_delivers
    # From case get samples
    # For every sample check if external and if so if it has hk bundle

    # TODO: Start the case if previous check return true else return
    # TODO: If case fails to start raise error else just return
    pass
