from datetime import datetime

from pydantic import BaseModel, Field

from cg.models.cg_config import LOG, CGConfig
from cg.services import transfer_to_cluster_service
from cg.store.models import (
    SAMPLE_NAME_MAXIMUM_LENGTH,
    SAMPLE_NAME_MINIMUM_LENGTH,
    SAMPLE_NAME_PATTERN,
    Customer,
)
from cg.store.store import Store


class ExternalSampleUploadedEvent(BaseModel):
    customer: str = Field(alias="cg.customer")
    customer_uploaded_at: datetime
    sample_name: str = Field(
        pattern=SAMPLE_NAME_PATTERN,
        min_length=SAMPLE_NAME_MINIMUM_LENGTH,
        max_length=SAMPLE_NAME_MAXIMUM_LENGTH,
        alias="cg.sample_name",
    )


def handle(config: CGConfig, event_payload: dict) -> None:
    """
    Add an entry to the ExternalSample table corresponding to the sample name received in the
    payload. If an order with the external sample has already been placed, trigger the transfer
    of the sample files from the delivery server to the internal cluster.
    """
    event = ExternalSampleUploadedEvent.model_validate(event_payload)
    status_db: Store = config.status_db
    customer: Customer = status_db.get_customer_by_internal_id_strict(event.customer)
    status_db.add_external_sample(
        customer_id=customer.id,
        sample_name=event.sample_name,
        customer_uploaded_at=event.customer_uploaded_at,
    )
    LOG.info(
        f"Added external sample {event.sample_name} for customer {event.customer} to the database."
    )
    if sample := status_db.get_sample_by_customer_and_name(
        customer_entry_id=[customer.id], sample_name=event.sample_name
    ):
        transfer_to_cluster_service.transfer_sample(cg_config=config, sample=sample)
        LOG.info(f"Transfer of sample {event.customer}/{event.sample_name} successfully started.")
