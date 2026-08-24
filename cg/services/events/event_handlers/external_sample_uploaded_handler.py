from datetime import datetime

from cg.models.cg_config import CGConfig
from cg.store.models import Customer
from cg.store.store import Store


def handle(config: CGConfig, data: dict):
    status_db: Store = config.status_db
    customer: Customer = status_db.get_customer_by_internal_id_strict(data["customer"])
    customer_uploaded_at = datetime.strptime(data["customer_uploaded_at"], "%Y-%m-%dT%H:%M:%SZ")
    status_db.add_external_sample(
        customer_id=customer.id,
        sample_name=data["sample_name"],
        customer_uploaded_at=customer_uploaded_at,
    )
    # TODO check if sample or order exist if so trigger download
    # TODO raise or return success
    pass
