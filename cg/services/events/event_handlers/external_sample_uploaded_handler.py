from datetime import datetime

from cg.models.cg_config import CGConfig
from cg.services import transfer_to_cluster_service
from cg.store.models import Customer
from cg.store.store import Store
from pydantic import BaseModel


class ExternalSampleUploadedEvent(BaseModel):
    customer: str
    customer_uploaded_at: datetime
    sample_name: str


def handle(config: CGConfig, data: dict):
    event = ExternalSampleUploadedEvent.model_validate(data)
    status_db: Store = config.status_db
    customer: Customer = status_db.get_customer_by_internal_id_strict(event.customer)
    # customer_uploaded_at = datetime.strptime(data["customer_uploaded_at"], "%Y-%m-%dT%H:%M:%SZ")
    status_db.add_external_sample(
        customer_id=customer.id,
        sample_name=event.sample_name,
        customer_uploaded_at=event.customer_uploaded_at,
    )
    if status_db.get_sample_by_customer_and_name(
        customer_entry_id=[customer.id], sample_name=event.sample_name
    ):
        transfer_to_cluster_service.transfer_sample(
            customer_internal_id=customer.internal_id, sample_name=event.sample_name
        )
