from pydantic import BaseModel

from cg.models.cg_config import CGConfig
from cg.services import transfer_to_cluster_service
from cg.store.models import Customer
from cg.store.store import Store


class ExternalSamplesOrderedEvent(BaseModel):
    customer: str
    sample_names: list[str]


def handle(config: CGConfig, event_payload: dict):
    event = ExternalSamplesOrderedEvent.model_validate(event_payload)
    status_db: Store = config.status_db
    customer: Customer = status_db.get_customer_by_internal_id_strict(internal_id=event.customer)
    # TODO: Loop over the samples in data
    for sample_name in event.sample_names:
        if status_db.get_external_sample(sample_name=sample_name, customer_id=customer.id):
            transfer_to_cluster_service.transfer_sample
    # TODO: If the sample is in the ExternalSample table
    # TODO: Trigger transfer (reuse previous code)

    pass
