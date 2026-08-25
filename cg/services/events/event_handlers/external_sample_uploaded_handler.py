from datetime import datetime

from pydantic import BaseModel, Field

from cg.models.cg_config import CGConfig
from cg.services import transfer_to_cluster_service
from cg.store.models import (
    SAMPLE_NAME_MAXIMUM_LENGTH,
    SAMPLE_NAME_MINIMUM_LENGTH,
    SAMPLE_NAME_PATTERN,
    Customer,
)
from cg.store.store import Store


class ExternalSampleUploadedEvent(BaseModel):
    customer: str
    customer_uploaded_at: datetime
    sample_name: str = Field(
        pattern=SAMPLE_NAME_PATTERN,
        min_length=SAMPLE_NAME_MINIMUM_LENGTH,
        max_length=SAMPLE_NAME_MAXIMUM_LENGTH,
    )


def handle(config: CGConfig, data: dict):
    event = ExternalSampleUploadedEvent.model_validate(data)
    status_db: Store = config.status_db
    customer: Customer = status_db.get_customer_by_internal_id_strict(event.customer)
    status_db.add_external_sample(
        customer_id=customer.id,
        sample_name=event.sample_name,
        customer_uploaded_at=event.customer_uploaded_at,
    )
    if status_db.get_sample_by_customer_and_name(
        customer_entry_id=[customer.id], sample_name=event.sample_name
    ):
        # TODO: Send in the cg config
        transfer_to_cluster_service.transfer_sample(
            customer_internal_id=customer.internal_id, sample_name=event.sample_name
        )
