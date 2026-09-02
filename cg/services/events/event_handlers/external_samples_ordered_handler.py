import logging

from pydantic import BaseModel, Field

from cg.models.cg_config import CGConfig
from cg.services import transfer_to_cluster_service
from cg.store.models import Customer, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class ExternalSamplesOrderedEvent(BaseModel):
    customer: str = Field(alias="status_db.customer")
    sample_names: list[str] = Field(alias="status_db.sample_names")


def handle(config: CGConfig, event_payload: dict):
    """
    Trigger the transfer of sample files for samples specified in the payload
    if they have an entry in the ExternalSample table.
    """
    event = ExternalSamplesOrderedEvent.model_validate(event_payload)
    status_db: Store = config.status_db
    customer: Customer = status_db.get_customer_by_internal_id_strict(internal_id=event.customer)
    for sample_name in event.sample_names:
        if status_db.get_external_sample(sample_name=sample_name, customer_id=customer.id):
            sample: Sample = status_db.get_sample_by_customer_and_name_strict(
                customer_entry_id=customer.id, sample_name=sample_name
            )
            transfer_to_cluster_service.transfer_sample(cg_config=config, sample=sample)
            LOG.info(f"Transfer of sample {event.customer}/{sample_name} successfully started.")
